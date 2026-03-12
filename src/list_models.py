from google import genai
from google.genai import types
import os
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GOOGLE_API_KEY"),
    http_options=types.HttpOptions(api_version="v1")
)

print("Embedding models your API key can access:")
for m in client.models.list():
    if "embed" in m.name.lower():
        print(f"  {m.name}")

print("\nAll models:")
for m in client.models.list():
    print(f"  {m.name}")



from google import genai

client = genai.Client(api_key="AIzaSyBYj8oXuInfL-J5PUH18PBlo083Mon8iz0")

response = client.models.embed_content(
    model="models/embedding-001",
    contents="Hello world"
)

print(len(response.embedding))