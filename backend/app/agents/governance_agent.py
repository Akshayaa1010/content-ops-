# app/agents/governance_agent.py
import json
from app.agents.llm_client import generate_json
from app.agents.knowledge_agent import search_knowledge
from app.pipeline.embeddings import embed_query

async def check_compliance(draft: str, brief: dict) -> dict:
    # 1. Retrieve relevant brand rules via RAG
    query_emb = await embed_query(f"Compliance check for: {draft[:200]}")
    relevant_rules = await search_knowledge(query_emb, limit=5)
    rules_context = "\n".join([f"- {r}" for r in relevant_rules])

    system_prompt = f"""
    You are a Governance Agent. 
    Review the draft against the content brief AND the specific brand rules retrieved from our policy database.
    
    BRAND RULES (RETRIEVED VIA RAG):
    {rules_context}
    
    Check for:
    1. STRICT adherence to the retrieved brand rules.
    2. Tone consistency and brief alignment.
    3. Accuracy and absence of exaggerated claims.
    
    Return a JSON object:
    {{
        "status": "PASS" | "FAIL",
        "score": 0.0 to 1.0,
        "violation_count": int,
        "report": "Detailed feedback citing specific rules.",
        "auto_fixes": "A compliant version if needed."
    }}
    """
    
    user_message = f"Brief: {json.dumps(brief)}\n\nDraft: {draft}"
    response_json = await generate_json(system_prompt, user_message)
    return json.loads(response_json)

async def sync_review_content(draft: dict) -> dict:
    import json
    import os
    from app.agents.llm_client import generate_json
    
    # Read policies directly
    policy_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "policies", "brand_policies.txt")
    try:
        with open(policy_path, "r", encoding="utf-8") as f:
            policies = f.read()
    except Exception as e:
        print(f"Warning: Could not read brand_policies.txt: {e}")
        policies = "Maintain a professional tone and do not exaggerate claims."

    system_prompt = f"""
    You are a strict Governance Agent for a global brand.
    Review the provided drafted content (a blog and a linkedin post) against the following BRAND POLICIES:
    
    {policies}
    
    Check for:
    1. Strict adherence to ALL the brand policies.
    2. Tone consistency and brief alignment.
    3. Accuracy and absence of exaggerated claims.
    
    Return a JSON object:
    {{
        "status": "PASS" | "FAIL",
        "feedback": "Detailed feedback citing specific rules that were violated. If PASS, provide positive confirmation."
    }}
    """
    
    user_message = f"Content Drafts:\n{json.dumps(draft, indent=2)}"
    try:
        response_json = await generate_json(system_prompt, user_message)
        return json.loads(response_json)
    except Exception as e:
        print(f"Governance review failed: {e}")
        return {"status": "FAIL", "feedback": str(e)}
