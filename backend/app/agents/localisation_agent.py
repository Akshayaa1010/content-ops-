# app/agents/localisation_agent.py
from app.agents.llm_client import generate
import asyncio

async def translate_text(text: str, source_lang: str = "en",
                          target_lang: str = "de") -> str:
    """
    Translates text using Groq LLM for high-quality Indian and European language localization.
    """
    lang_map = {
        "ta": "Tamil",
        "hi": "Hindi",
        "bn": "Bengali",
        "te": "Telugu",
        "ml": "Malayalam",
        "de": "German",
        "fr": "French",
        "es": "Spanish"
    }
    
    target_lang_name = lang_map.get(target_lang, target_lang)
    
    system_prompt = f"""
    You are a professional translator specializing in {target_lang_name}.
    Translate the provided English text into natural, fluent {target_lang_name}.
    Maintain the same tone, formatting, and SEO keywords as the original.
    Do NOT include any introductory or concluding remarks—only provide the translated text.
    """
    
    try:
        translated_text = await generate(system_prompt, text, max_tokens=2000)
        return translated_text.strip()
    except Exception as e:
        print(f"ERROR: Groq localization failed for {target_lang_name}: {e}")
        return text # Fallback to original English if Groq fails

async def localise_all(draft_text: str,
                        target_languages: list[str]) -> dict[str, str]:
    """
    Translates draft into multiple target languages in parallel.
    """
    print(f"LOCALIZING into {len(target_languages)} languages: {target_languages}")
    tasks = [translate_text(draft_text, "en", lang) for lang in target_languages]
    results = await asyncio.gather(*tasks)
    return dict(zip(target_languages, results))

if __name__ == "__main__":
    # Test block
    async def test():
        res = await localise_all("Hello, welcome to our AI-powered content platform.", ["ta", "hi"])
        print(res)
    asyncio.run(test())