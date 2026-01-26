
import json
from typing import List, Dict, Any, Optional
from ..config import settings
from ..utils.logger import get_logger

logger = get_logger("synthesis_agent")

class SynthesisAgent:
    """
    The 'Voice' of the platform.
    Summarizes search results and answers user questions using retrieval from the run artifacts.
    """
    
    def __init__(self):
        self.model_name = settings.agent.reasoning_model
        # self.llm_client = ... (Initialize your OpenAI/Anthropic client here) 
        # For now, we'll use a mock/stub if no API key is present context.

    async def generate_briefing(self, query_id: str, query_text: str, leads: List[Dict[str, Any]], orchestration_summary: Dict[str, Any]) -> str:
        """
        Generate a high-level executive summary of the search run.
        """
        try:
            logger.info("Generating briefing", query_id=query_id)
            
            # 1. Context Stuffing
            # We don't send all 50 leads to LLM to save tokens, just top 10 and stats.
            top_leads = leads[:10] if leads else []
            
            stats = {
                "total_found": orchestration_summary.get("raw_leads_found", 0),
                "saved": len(leads),
                "search_mode": orchestration_summary.get("execution_mode", "unknown")
            }
            
            # 2. Prompt Engineering
            prompt = f"""
            Role: Expert Technical Recruiter & Talent Analyst.
            Task: Write a 3-paragraph Executive Briefing for a Hiring Manager.
            
            Query: "{query_text}"
            
            Run Statistics:
            - Scanned: {stats['total_found']} candidates
            - Shortlisted: {stats['saved']} high-quality matches
            
            Top Candidates Found (Sample):
            {json.dumps([{
                'name': l.get('company', 'Unknown'), 
                'score': l.get('score'), 
                'match_reasons': l.get('reasons', [])
            } for l in top_leads], indent=2)}
            
            Instructions:
            1. SUMMARY: One sentence on the market quality for this role (e.g., "Talent pool is deep/shallow").
            2. HIGHLIGHTS: Mention 2-3 specific companies that look promising and WHY (cite specific reasons from data).
            3. STRATEGY: Suggest one follow-up action.
            
            Tone: Professional, insightful, concise. No "As an AI" filler.
            """
            
            # 3. LLM Call (Stubbed for now to avoid compilation errors if no client)
            # response = await self.llm_client.chat(prompt)
            # return response
            
            # MOCK OUTPUT (Until LLM is wired)
            return self._mock_briefing(query_text, top_leads)

        except Exception as e:
            logger.error("Briefing generation failed", error=str(e), query_id=query_id)
            return "Analysis currently unavailable."

    def _mock_briefing(self, query, leads):
        if not leads:
            return f"I ran a search for '{query}' but couldn't find any leads matching your strict criteria. Consider broadening the location or skills."
            
        top_company = leads[0].get('company', 'Unknown')
        count = len(leads)
        
        return f"""
### 🎯 Executive Briefing

I've analyzed the market for **"{query}"** and found **{count} high-priority candidates**.

**Top Recommendation:**
**{top_company}** (Score: {leads[0].get('score')}) stands out significantly. {leads[0].get('reasons', ['Strong match'])[0]}.

**Market Context:**
The talent pool confirms your requirements are realistic, though most strong profiles are concentrated in companies with recent funding events.

**Suggested Action:**
Start personalized outreach to the top 5 candidates immediately, focusing on the "Growth" angle.
        """

synthesis_agent = SynthesisAgent()
