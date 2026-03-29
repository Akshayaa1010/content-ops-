# app/pipeline/embeddings.py
import asyncio

_model = None

def get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        # Downloads ~90MB on first run, cached after that
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model

async def embed_texts(texts: list[str]) -> list[list[float]]:
    model = get_model()
    loop = asyncio.get_event_loop()
    # Run in thread pool to avoid blocking the async event loop
    embeddings = await loop.run_in_executor(
        None, lambda: model.encode(texts, batch_size=32)
    )
    return [e.tolist() for e in embeddings]

async def embed_query(query: str) -> list[float]:
    results = await embed_texts([query])
    return results[0]