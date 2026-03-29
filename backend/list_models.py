from groq import Groq
from app.config.settings import settings

def list_models():
    client = Groq(api_key=settings.groq_api_key)
    print("Available Groq Models:")
    try:
        models = client.models.list()
        for m in models.data:
            print(f"- {m.id}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_models()
