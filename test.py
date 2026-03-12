from pathlib import Path
from dotenv import load_dotenv
from google import genai
import os

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env", override=True)

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

for model in client.models.list():
    print(model.name)


response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Say hello"
)

print(response.text)