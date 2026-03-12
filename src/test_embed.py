import os
from typing import List

from dotenv import load_dotenv
from google import genai
from google.genai import types
from langchain_core.embeddings import Embeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
from pathlib import Path

dotenv_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path)




# ──────────────────────────────────────────────
# Custom embeddings wrapper — NO langchain_google_genai,
# NO torch, NO transformers. Calls Google SDK directly.
# ──────────────────────────────────────────────
class GoogleEmbeddings(Embeddings):
    def __init__(self, model: str = "models/gemini-embedding-001"):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment. Check your .env file.")
        self.model = model
        self.client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(api_version="v1")
        )

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        result = self.client.models.embed_content(
            model=self.model,
            contents=texts,
            config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
        )
        return [e.values for e in result.embeddings]

    def embed_query(self, text: str) -> List[float]:
        result = self.client.models.embed_content(
            model=self.model,
            contents=text,
            config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY")
        )
        return result.embeddings[0].values


def get_embeddings() -> GoogleEmbeddings:
    return GoogleEmbeddings(model="embedding-001")


def get_pinecone_client() -> Pinecone:
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        raise ValueError("PINECONE_API_KEY not found in environment. Check your .env file.")
    return Pinecone(api_key=api_key)


def ensure_index_exists(pc: Pinecone, index_name: str):
    existing_indexes = [index.name for index in pc.list_indexes()]
    if index_name not in existing_indexes:
        print(f"  Creating Pinecone index: '{index_name}'...")
        pc.create_index(
            name=index_name,
            dimension=768,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
        print(f"  Index '{index_name}' created successfully")
    else:
        print(f"  Index '{index_name}' already exists — using existing index")


def upload_to_pinecone(chunks: list, namespace: str = "rbs") -> PineconeVectorStore:
    index_name = os.getenv("PINECONE_INDEX_NAME", "rbs-chatbot")

    print(f"\n  Connecting to Pinecone...")
    pc = get_pinecone_client()
    ensure_index_exists(pc, index_name)

    print(f"\n  Loading embedding model...")
    emb = get_embeddings()

    print(f"\n  Uploading {len(chunks)} chunks to Pinecone...")
    print(f"  This will take ~{len(chunks) // 10 + 1} seconds...")

    vs = PineconeVectorStore.from_documents(
        chunks, emb, index_name=index_name, namespace=namespace
    )

    print(f"  Successfully uploaded {len(chunks)} chunks!")
    print(f"  Index: {index_name} | Namespace: {namespace}")
    return vs


def load_vectorstore(namespace: str = "rbs") -> PineconeVectorStore:
    index_name = os.getenv("PINECONE_INDEX_NAME", "rbs-chatbot")
    emb = get_embeddings()
    vs = PineconeVectorStore(
        index_name=index_name,
        embedding=emb,
        namespace=namespace
    )
    print(f"  Connected to Pinecone index: '{index_name}' (namespace: {namespace})")
    return vs


if __name__ == "__main__":
    from src.loader import prepare_all_chunks
    chunks = prepare_all_chunks()
    vs = upload_to_pinecone(chunks)
    print("\nTest query: 'data science programme duration'")
    results = vs.similarity_search("data science programme duration", k=3)
    for i, r in enumerate(results):
        print(f"\nResult {i+1} [{r.metadata.get('campus', '?')}]:")
        print(r.page_content[:200])