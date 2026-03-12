import os
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pathlib import Path

# Path to your .env
dotenv_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path)

print("GOOGLE_API_KEY loaded:", os.getenv("GOOGLE_API_KEY") is not None)
print("PINECONE_API_KEY loaded:", os.getenv("PINECONE_API_KEY") is not None)

def get_embeddings():
    return GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key="AIzaSyBYj8oXuInfL-J5PUH18PBlo083Mon8iz0"
    )

def get_pinecone_client():
    return Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

def ensure_index(pc: Pinecone, name: str):
    existing = [i.name for i in pc.list_indexes()]
    if name in existing:
        print(f"Deleting existing index {name} to match new dimension")
        pc.delete_index(name)
    pc.create_index(
        name=name,
        dimension=3072,  # <-- match gemini-embedding-001
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )
    print(f"Created Pinecone index: {name}")

def upload_to_pinecone(chunks: list, namespace="rbs") -> PineconeVectorStore:
    name = os.getenv("PINECONE_INDEX_NAME", "rbs-chatbot")
    pc   = get_pinecone_client()
    ensure_index(pc, name)
    emb  = get_embeddings()
    print(f"Uploading {len(chunks)} chunks → Pinecone [{name}:{namespace}]")
    vs = PineconeVectorStore.from_documents(chunks, emb, index_name=name, namespace=namespace)
    print("Upload complete")
    return vs

def load_vectorstore(namespace="rbs") -> PineconeVectorStore:
    name = os.getenv("PINECONE_INDEX_NAME", "rbs-chatbot")
    emb  = get_embeddings()
    vs   = PineconeVectorStore(index_name=name, embedding=emb, namespace=namespace)
    print(f"Connected to Pinecone [{name}:{namespace}]")
    return vs
