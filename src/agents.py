import os
from unittest import result
from dotenv import load_dotenv

from langchain_core import messages
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent  
from langgraph.checkpoint.memory import MemorySaver

from src.tools import get_tools

load_dotenv()

SYSTEM_PROMPT = """You are an expert admissions advisor for Rome Business School (RBS), \
specialising exclusively in the Executive Master in Data Science Management programme.

You serve prospective students asking about:
- The RBS Nigeria campus (local African delivery, fees in Naira)
- The RBS Italy campus (European delivery, international accreditation)
- Comparisons between both campuses

PERSONALITY: Warm, knowledgeable, encouraging, and professional.

TOOL SELECTION RULES — follow these strictly:
1. Fee questions          → ALWAYS use rbs_fee_lookup
2. Admission questions    → ALWAYS use rbs_admission_checker
3. Curriculum questions   → ALWAYS use rbs_curriculum_lookup
4. Career questions       → ALWAYS use rbs_career_outcomes
5. Comparison questions   → ALWAYS use rbs_compare_campuses
6. Latest news/updates    → ALWAYS use rbs_web_search
7. General programme info → use rbs_programme_search
8. Background concepts    → use general_knowledge (NOT for RBS-specific info)
9. Off-topic questions    → politely decline and redirect to programme topics

ANSWER RULES:
- ONLY use information returned by the tools. Never invent fees, dates, or names.
- If a tool returns no results, say so and give the admissions contact.
- Always label which campus (Nigeria/Italy) your information comes from.
- For comparisons, use a clear table or labelled sections.

CONTACTS (use when tools return no results):
- Nigeria: https://romebusinessschool.ng
- Italy:   https://romebusinessschool.com"""


def get_llm():
    """Initialise Gemini with low temperature for factual accuracy."""
    return ChatGoogleGenerativeAI(
        model="models/gemini-2.5-flash",       
        google_api_key="AIzaSyBYj8oXuInfL-J5PUH18PBlo083Mon8iz0",
        temperature=0.2,
        convert_system_message_to_human=True,
        timeout=60,
        max_retries=2
    )


# Module-level checkpointer so run_agent can access it
checkpointer = MemorySaver()


def build_agent():
    """
    Build the LangGraph ReAct agent with all tools.

    Returns:
        A compiled LangGraph graph ready to invoke.
    """
    print("Building RBS LangGraph Agent...")

    tools = get_tools()
    print(f"{len(tools)} tools loaded: {[t.name for t in tools]}")

    llm = get_llm()
    print("Gemini loaded")

    agent = create_react_agent(    
        model=llm,
        tools=tools,
        prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer,  
    )

    print("LangGraph agent compiled and ready!\n")
    return agent


def run_agent(agent, question: str, thread_id: str = "default") -> dict:
    """
    Send a question to the agent and return a structured response.

    Args:
        agent:     The compiled LangGraph agent from build_agent()
        question:  The user's question string
        thread_id: Unique ID for this conversation session.

    Returns:
        dict with answer, tools_used, steps, and state keys.
    """
    config = {"configurable": {"thread_id": thread_id}}

    try:
        result = agent.invoke(
            {"messages": [("user", question)]},
            config=config,
        )

        messages = result.get("messages", [])
        last_msg = messages[-1] if messages else None

        if last_msg is None:
            answer = "No response generated."
        elif isinstance(last_msg.content, str):
            # Normal case — plain string, use directly
            answer = last_msg.content
        elif isinstance(last_msg.content, list):
            # Block format — find all 'text' type blocks and join them
             answer = "\n".join(
            block.get("text", "")
            for block in last_msg.content
                if isinstance(block, dict) and block.get("type") == "text"
             )
        else:
            answer = str(last_msg.content)

        tools_used = []
        steps = []
        for msg in messages:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    tool_name = tc.get("name", "unknown")
                    tool_input = tc.get("args", {})
                    tools_used.append(tool_name)
                    steps.append({"tool": tool_name, "input": tool_input})

        return {
            "answer": answer,
            "tools_used": list(dict.fromkeys(tools_used)),
            "steps": steps,
            "state": result,
        }

    except Exception as e:
        return {
            "answer": (
                f"I encountered an error processing your question. "
                f"Please try rephrasing it, or contact admissions directly:\n"
                f"https://romebusinessschool.ng\n\nError: {str(e)}"
            ),
            "tools_used": [],
            "steps": [],
            "state": {},
        }