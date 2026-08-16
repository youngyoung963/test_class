from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client()

interaction = client.interactions.create(
    model="gemini-3.5-flash",
    input="天空為什麼是藍的"
)

print(interaction.output_text)