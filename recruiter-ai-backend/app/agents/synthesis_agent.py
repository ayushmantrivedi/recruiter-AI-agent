
import json
import os
import httpx
from typing import List, Dict, Any, Optional
from ..config import settings
from ..utils.logger import get_logger

logger = get_logger("synthesis_agent")


class SynthesisAgent:
    """
    The 'Voice' of the platform.
    Generates executive briefings using LLM via OpenRouter API.
    """
    
    def __init__(self):
        # OpenRouter configuration (reads directly from env for flexibility)
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.model_name = os.getenv("OPENROUTER_MODEL", "openai/gpt-3.5-turbo")
        self.api_base = "https://openrouter.ai/api/v1/chat/completions"
        
        if not self.api_key:
            logger.warning("OPENROUTER_API_KEY not set. SynthesisAgent will use fallback responses.")
        else:
            logger.info("SynthesisAgent initialized", model=self.model_name)

    async def generate_briefing(
        self, 
        query_id: str, 
        query_text: str, 
        leads: List[Dict[str, Any]], 
        orchestration_summary: Dict[str, Any]
    ) -> str:
        """
        Generate a high-level executive summary of the search run using OpenRouter.
        """
        try:
            logger.info("Generating briefing", query_id=query_id, model=self.model_name)
            
            # 1. Prepare Context (Token-optimized: Top 10 leads only)
            top_leads = leads[:10] if leads else []
            
            stats = {
                "total_scanned": orchestration_summary.get("raw_leads_found", len(leads)),
                "shortlisted": len(leads),
                "search_mode": orchestration_summary.get("execution_mode", "standard")
            }
            
            # 2. Build Prompt
            system_prompt = """You are an expert technical recruiter and talent market analyst. 
Your job is to provide concise, insightful executive briefings to hiring managers based on search results.
Be direct, professional, and data-driven. Never say "As an AI" or similar disclaimers.
Format your response in markdown with clear sections."""

            user_prompt = f"""Analyze these search results and write a brief executive summary.

**Search Query:** "{query_text}"

**Statistics:**
- Total candidates scanned: {stats['total_scanned']}
- High-quality matches found: {stats['shortlisted']}

**Top Candidates:**
{json.dumps([{
    'company': l.get('company', 'Unknown'),
    'score': l.get('score', 0),
    'key_signals': l.get('reasons', ['Match found'])[:2]
} for l in top_leads], indent=2)}

**Your Task:**
Write a 3-paragraph briefing covering:
1. **Market Assessment**: Is the talent pool strong or weak for this query? Why?
2. **Top Recommendations**: Highlight 2-3 specific companies and why they stand out (cite the signals).
3. **Next Steps**: One actionable recommendation.

Keep it under 200 words. Be specific, not generic."""

            # 3. Call OpenRouter API
            if not self.api_key:
                logger.warning("No API key, using fallback", query_id=query_id)
                return self._fallback_briefing(query_text, top_leads, stats)
            
            briefing = await self._call_openrouter(system_prompt, user_prompt)
            
            if briefing:
                logger.info("Briefing generated successfully", query_id=query_id, length=len(briefing))
                return briefing
            else:
                return self._fallback_briefing(query_text, top_leads, stats)

        except Exception as e:
            logger.error("Briefing generation failed", error=str(e), query_id=query_id)
            return f"Analysis temporarily unavailable. Error: {str(e)}"

    async def _call_openrouter(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """Make the actual OpenRouter API call."""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.api_base,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "http://localhost:8001",  # Required by OpenRouter
                        "X-Title": "Recruiter AI"  # Optional app name
                    },
                    json={
                        "model": self.model_name,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": 0.7,
                        "max_tokens": 500
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    logger.error("OpenRouter API error", 
                               status=response.status_code, 
                               body=response.text[:500])
                    return None
                    
        except Exception as e:
            logger.error("OpenRouter API call failed", error=str(e))
            return None

    def _fallback_briefing(self, query: str, leads: List[Dict], stats: Dict) -> str:
        """Fallback when API is unavailable - uses template with actual data."""
        if not leads:
            return f"""### ⚠️ No Results Found

I searched for **"{query}"** but couldn't find matching candidates in the current data sources.

**Suggestions:**
- Try broadening your search criteria
- Check if the role/skills are spelled correctly
- Consider expanding the geographic scope"""
        
        # Build dynamic content from actual lead data
        top_companies = [l.get('company', 'Unknown') for l in leads[:3]]
        top_reasons = []
        for l in leads[:3]:
            reasons = l.get('reasons', [])
            if reasons:
                top_reasons.append(f"- **{l.get('company')}**: {reasons[0]}")
        
        reasons_text = "\n".join(top_reasons) if top_reasons else "- Strong match signals detected"
        
        return f"""### Executive Briefing

**Query:** "{query}"  
**Results:** Found {stats['shortlisted']} candidates from {stats['total_scanned']} scanned.

**Top Matches:**
{reasons_text}

**Market Assessment:**
Based on {len(leads)} qualified matches, the talent pool for this query appears {"healthy" if len(leads) >= 3 else "limited"}. 
Top companies showing hiring signals: {', '.join(top_companies)}.

**Recommended Action:**
Prioritize outreach to the highest-scoring candidates. Consider reaching out within 48 hours as these signals indicate active hiring."""


# Global instance
synthesis_agent = SynthesisAgent()
