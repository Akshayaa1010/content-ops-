# app/agents/intelligence_agent.py
import json
from app.agents.llm_client import generate_json

async def suggest_strategy(brief: dict) -> dict:
    system_prompt = """
    You are a Content Intelligence Agent. 
    Analyze the provided content brief and suggest optimizations based on simulated engagement patterns.
    
    Engagement Signals (Simulated):
    - Topic: "AI" - High LinkedIn engagement, low Blog SEO.
    - Format: "Technical" - High Sales Collateral usage, low Social shares.
    - Tone: "Authoritative" - High trust score in B2B.
    
    Suggest:
    1. Optimal Channels (if missing).
    2. Best Format.
    3. Target Audience refinement.
    
    Return a JSON object:
    {
        "suggested_channels": ["LinkedIn", "X", "CMS"],
        "reasoning": "Brief explanation of the strategy.",
        "adjusted_brief": { ... refined copy of the brief ... }
    }
    """
    
    user_message = f"Current Brief: {json.dumps(brief)}"
    response_json = await generate_json(system_prompt, user_message)
    return json.loads(response_json)

async def get_performance_summary() -> dict:
    # Simulates pulling data from external analytics
    return {
        "avg_engagement_lift": "+24%",
        "best_performing_channel": "LinkedIn",
        "localisation_efficiency": "92%"
    }
