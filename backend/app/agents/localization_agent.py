import asyncio

LANGUAGE_NAMES = {
    "ta": "Tamil",
    "hi": "Hindi",
    "bn": "Bengali",
    "te": "Telugu",
    "ml": "Malayalam",
    # Keep legacy European codes working too
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "nl": "Dutch",
}

async def translate_text(text: str, target_lang: str) -> str:
    """
    Translates text to the target language using Groq LLM.
    Works for any language including Indian languages (Tamil, Hindi, Bengali, Telugu, Malayalam).
    """
    from app.agents.llm_client import generate
    lang_name = LANGUAGE_NAMES.get(target_lang, target_lang)
    system_prompt = (
        f"You are an expert translator. Translate the following English content into {lang_name}. "
        f"Preserve the original formatting, paragraph structure, and meaning exactly. "
        f"Output ONLY the translated text with NO explanations, NO English, NO preamble."
    )
    try:
        translated = await generate(system_prompt, text, max_tokens=2000)
        return translated.strip()
    except Exception as e:
        print(f"Translation error for {target_lang} ({lang_name}): {e}")
        return f"[Translation to {lang_name} failed: {str(e)}]"

async def translate_multiple(text: str, languages: list[str]) -> dict[str, str]:
    """
    Translates text into multiple languages concurrently using Groq.
    """
    tasks = [translate_text(text, lang) for lang in languages]
    results = await asyncio.gather(*tasks)
    return dict(zip(languages, results))
