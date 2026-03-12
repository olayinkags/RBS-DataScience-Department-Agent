
import os
from typing import Annotated
from typing_extensions import TypedDict

from dotenv import load_dotenv

from langchain_core.tools   import tool, InjectedToolCallId
from langchain_core.messages import ToolMessage
from langgraph.types         import Command
from langgraph.prebuilt      import InjectedState

from langchain_community.tools import DuckDuckGoSearchRun
from src.embedder import load_vectorstore

load_dotenv()


class RBSAgentState(TypedDict):
    # The conversation messages (user, assistant, tool messages)
    messages: list

    # Which campus was most recently searched ("nigeria", "italy", "both")
    last_campus_searched: str

    # Which tool was called last (useful for debugging + UI display)
    last_tool_used: str

    # The raw retrieved chunks from the last Pinecone search
    last_retrieved_context: str

    # Whether we found relevant content in Pinecone
    context_found: bool

    # The topic of the last search (for follow-up questions)
    last_search_topic: str



_vectorstore = None

def get_vs():
    """Lazy-load the Pinecone vectorstore — only connects on first call."""
    global _vectorstore
    if _vectorstore is None:
        _vectorstore = load_vectorstore(namespace="rbs")
    return _vectorstore


def _format_docs(docs: list, label: str = "") -> str:
    """Turn a list of LangChain Documents into a readable string."""
    if not docs:
        return f"[{label}] No relevant content found in knowledge base."
    chunks = []
    for i, doc in enumerate(docs, 1):
        campus = doc.metadata.get("campus", "unknown").upper()
        source = doc.metadata.get("source", "")
        chunks.append(
            f"[{campus} — Result {i}]\n"
            f"Source: {source}\n"
            f"{doc.page_content}"
        )
    return "\n\n---\n\n".join(chunks)


@tool
def rbs_programme_search(
    query: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    """
    Search the full RBS Executive Master in Data Science Management
    knowledge base (both Nigeria and Italy content combined).

    Use this for general questions about the programme that are not
    specifically about fees, admissions, curriculum, or career outcomes.

    Args:
        query: Natural language search query about the RBS programme.
    """
    docs    = get_vs().similarity_search(query, k=5)
    context = _format_docs(docs, "PROGRAMME SEARCH")
    found   = bool(docs) and "No relevant" not in context

    return Command(update={
        # Update shared state so the agent and other tools can see results
        "last_tool_used":        "rbs_programme_search",
        "last_campus_searched":  "both",
        "last_retrieved_context": context,
        "last_search_topic":     query,
        "context_found":         found,

        # Append a proper ToolMessage to the conversation history
        "messages": [ToolMessage(
            content=context,
            tool_call_id=tool_call_id,
        )],
    })



@tool
def rbs_compare_campuses(
    query: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    """
    Retrieve information from BOTH RBS Nigeria AND RBS Italy campuses
    for the same query. Returns clearly labelled results for each campus,
    enabling a structured side-by-side comparison.

    Use when the user asks to compare campuses, asks about differences,
    or asks a question that applies to both Nigeria and Italy.

    Args:
        query: The aspect to compare (e.g. 'fees', 'duration', 'accreditation').
    """
    vs = get_vs()

    # Search each campus separately using Pinecone metadata filter
    nigeria_docs = vs.similarity_search(query, k=4, filter={"campus": "nigeria"})
    italy_docs   = vs.similarity_search(query, k=4, filter={"campus": "italy"})

    nigeria_text = _format_docs(nigeria_docs, "RBS NIGERIA")
    italy_text   = _format_docs(italy_docs,   "RBS ITALY")

    context = (
        "=== RBS NIGERIA ===\n" + nigeria_text +
        "\n\n=== RBS ITALY ===\n" + italy_text
    )

    found = bool(nigeria_docs) or bool(italy_docs)

    return Command(update={
        "last_tool_used":         "rbs_compare_campuses",
        "last_campus_searched":   "both",
        "last_retrieved_context": context,
        "last_search_topic":      query,
        "context_found":          found,

        "messages": [ToolMessage(
            content=context,
            tool_call_id=tool_call_id,
        )],
    })


@tool
def rbs_fee_lookup(
    campus: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    """
    Look up tuition fees, costs, payment plans, and financial information
    for the RBS Executive Master in Data Science Management.

    Args:
        campus: Which campus to look up — 'nigeria', 'italy', or 'both'.
    """
    vs    = get_vs()
    query = "tuition fees cost payment plan instalment scholarship financial"

    if campus == "both":
        ng_docs = vs.similarity_search(query, k=4, filter={"campus": "nigeria"})
        it_docs = vs.similarity_search(query, k=4, filter={"campus": "italy"})
        context = (
            "=== RBS NIGERIA — FEES ===\n" + _format_docs(ng_docs, "NIGERIA FEES") +
            "\n\n=== RBS ITALY — FEES ===\n"  + _format_docs(it_docs, "ITALY FEES")
        )
        found = bool(ng_docs) or bool(it_docs)
    else:
        # Normalise campus value in case model passes unexpected strings
        campus = campus.lower().strip()
        if campus not in ("nigeria", "italy"):
            campus = "nigeria"  # safe default

        docs    = vs.similarity_search(query, k=5, filter={"campus": campus})
        context = _format_docs(docs, f"{campus.upper()} FEES")
        found   = bool(docs)

    return Command(update={
        "last_tool_used":         "rbs_fee_lookup",
        "last_campus_searched":   campus,
        "last_retrieved_context": context,
        "last_search_topic":      "fees",
        "context_found":          found,

        "messages": [ToolMessage(
            content=context,
            tool_call_id=tool_call_id,
        )],
    })



@tool
def rbs_admission_checker(
    query: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    """
    Search for admission requirements, eligibility criteria, required
    documents, application deadlines, and the application process for
    the RBS Executive Master in Data Science Management programme.

    Use for any question about: how to apply, who can apply, what
    qualifications are needed, application documents, intake dates.

    Args:
        query: Specific aspect of admissions to search for.
    """
    # Enrich the query with admission-specific keywords for better retrieval
    enriched = f"admission requirements eligibility application process documents {query}"
    docs     = get_vs().similarity_search(enriched, k=5)
    context  = _format_docs(docs, "ADMISSIONS")
    found    = bool(docs)

    return Command(update={
        "last_tool_used":         "rbs_admission_checker",
        "last_campus_searched":   "both",
        "last_retrieved_context": context,
        "last_search_topic":      f"admissions: {query}",
        "context_found":          found,

        "messages": [ToolMessage(
            content=context,
            tool_call_id=tool_call_id,
        )],
    })



@tool
def rbs_curriculum_lookup(
    topic: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    """
    Look up the curriculum, modules, subjects, course content,
    specialisations, and learning outcomes for the RBS Executive
    Master in Data Science Management programme.

    Use for questions about: what is taught, which subjects are covered,
    data science topics, tools used, programme structure, specialisations.

    Args:
        topic: Specific subject or 'all modules' for full curriculum overview.
    """
    enriched = f"curriculum modules subjects data science {topic} learning outcomes syllabus"
    docs     = get_vs().similarity_search(enriched, k=6)
    context  = _format_docs(docs, "CURRICULUM")
    found    = bool(docs)

    return Command(update={
        "last_tool_used":         "rbs_curriculum_lookup",
        "last_campus_searched":   "both",
        "last_retrieved_context": context,
        "last_search_topic":      f"curriculum: {topic}",
        "context_found":          found,

        "messages": [ToolMessage(
            content=context,
            tool_call_id=tool_call_id,
        )],
    })



@tool
def rbs_career_outcomes(
    query: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    """
    Search for career services, job placement rates, alumni network,
    salary outcomes, and professional development opportunities for
    RBS Executive Master in Data Science Management graduates.

    Use for: career prospects after graduation, employer partnerships,
    alumni success stories, ROI of the programme, job titles obtained.

    Args:
        query: Specific career aspect to search for.
    """
    enriched = f"career outcomes job placement alumni network salary employment {query}"
    docs     = get_vs().similarity_search(enriched, k=5)
    context  = _format_docs(docs, "CAREER OUTCOMES")
    found    = bool(docs)

    return Command(update={
        "last_tool_used":         "rbs_career_outcomes",
        "last_campus_searched":   "both",
        "last_retrieved_context": context,
        "last_search_topic":      f"careers: {query}",
        "context_found":          found,

        "messages": [ToolMessage(
            content=context,
            tool_call_id=tool_call_id,
        )],
    })



_ddg = DuckDuckGoSearchRun()

@tool
def rbs_web_search(
    query: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    """
    Search the live internet for the latest news and updates about
    Rome Business School Nigeria or Italy. Use when the user asks
    about recent events, new announcements, updated intake dates,
    or anything that may not yet be in the knowledge base.

    Args:
        query: Search terms about RBS to find on the web.
    """
    search_query = f"Rome Business School Nigeria {query}"
    try:
        result = _ddg.run(search_query)
        content = f"[WEB SEARCH: '{search_query}']\n\n{result}"
        found   = True
    except Exception as e:
        content = f"Web search failed: {e}. Try rephrasing or use rbs_programme_search."
        found   = False

    return Command(update={
        "last_tool_used":         "rbs_web_search",
        "last_campus_searched":   "web",
        "last_retrieved_context": content,
        "last_search_topic":      f"web: {query}",
        "context_found":          found,

        "messages": [ToolMessage(
            content=content,
            tool_call_id=tool_call_id,
        )],
    })



@tool
def general_knowledge(
    query: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    """
    Answer general background questions about data science, business
    analytics, executive education, or career paths — questions that
    do NOT require RBS-specific information from the knowledge base.

    Use ONLY for broad educational or definitional questions.
    Do NOT use this for anything RBS-specific (fees, admissions, etc.).

    Args:
        query: The general background question to answer.
    """
    # Signal to the agent to answer from its own knowledge
    content = (
        f"[GENERAL KNOWLEDGE]\n"
        f"Query: {query}\n\n"
        f"This is a general background question. "
        f"Answer it from your own knowledge about the topic. "
        f"Keep it concise and relevant to someone considering "
        f"a Data Science management programme."
    )

    return Command(update={
        "last_tool_used":         "general_knowledge",
        "last_campus_searched":   "none",
        "last_retrieved_context": content,
        "last_search_topic":      f"general: {query}",
        "context_found":          True,

        "messages": [ToolMessage(
            content=content,
            tool_call_id=tool_call_id,
        )],
    })



def get_tools() -> list:
    """Return all 8 tools for the RBS agent."""
    return [
        rbs_programme_search,
        rbs_compare_campuses,
        rbs_fee_lookup,
        rbs_admission_checker,
        rbs_curriculum_lookup,
        rbs_career_outcomes,
        rbs_web_search,
        general_knowledge,
    ]
