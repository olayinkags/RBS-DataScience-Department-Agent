from google import genai

client = genai.Client(api_key="AIzaSyBYj8oXuInfL-J5PUH18PBlo083Mon8iz0")

print("Testing models...")
for m in client.models.list():
    print(m.name)