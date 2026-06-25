"""
AI scoring engine using OpenAI structured outputs + Anthropic for reasoning.
"""
import json
import time
from dataclasses import dataclass
from typing import Any

from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from backend.config import get_settings

settings = get_settings()


@dataclass
class ContactScoreResult:
    overall_score: float        # 0-100
    seniority_score: float      # 0-100, based on title/level
    engagement_score: float     # 0-100, based on completeness of profile
    fit_score: float            # 0-100, ICP fit
    technology_score: float     # 0-100, relevant tech stack
    industry_score: float       # 0-100, target industry match
    score_breakdown: dict       # detailed reasoning per dimension
    model_used: str
    tokens_used: int
    latency_ms: int


@dataclass 
class CompanyScoreResult:
    overall_score: float
    company_score: float        # size/revenue/growth signals
    technology_score: float     # tech stack modernity
    industry_score: float       # target industry alignment
    engagement_score: float     # data completeness
    fit_score: float            # ICP fit
    seniority_score: float      # (set to 0 for companies)
    score_breakdown: dict
    model_used: str
    tokens_used: int
    latency_ms: int


class AIScorer:
    """
    Scores leads using AI. Tries Anthropic claude-haiku-4-5-20251001 first for cost efficiency,
    falls back to OpenAI gpt-4o-mini if Anthropic unavailable.
    """
    
    def __init__(self):
        self.anthropic = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY) if settings.ANTHROPIC_API_KEY else None
        self.openai = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
    
    async def score_contact(self, contact_data: dict, icp_profile: dict | None = None) -> ContactScoreResult:
        """
        Score a contact against ideal customer profile.
        contact_data: {first_name, last_name, email, designation, department, seniority, 
                       company_name, company_industry, company_size, technologies: []}
        icp_profile: {target_industries: [], target_seniority: [], target_company_size: str,
                      required_technologies: [], keywords: []}
        """
        start = time.time()
        
        prompt = _build_contact_scoring_prompt(contact_data, icp_profile)
        
        if self.anthropic and settings.ANTHROPIC_API_KEY:
            result = await self._score_with_anthropic(prompt, "contact")
        elif self.openai and settings.OPENAI_API_KEY:
            result = await self._score_with_openai(prompt, "contact")
        else:
            result = _rule_based_contact_score(contact_data, icp_profile)
        
        latency_ms = int((time.time() - start) * 1000)
        result["latency_ms"] = latency_ms
        
        return ContactScoreResult(**result)
    
    async def score_company(self, company_data: dict, icp_profile: dict | None = None) -> CompanyScoreResult:
        """
        Score a company against ideal customer profile.
        company_data: {name, domain, industry, employee_count, annual_revenue, 
                       technologies: [], country, description}
        """
        start = time.time()
        
        prompt = _build_company_scoring_prompt(company_data, icp_profile)
        
        if self.anthropic and settings.ANTHROPIC_API_KEY:
            result = await self._score_with_anthropic(prompt, "company")
        elif self.openai and settings.OPENAI_API_KEY:
            result = await self._score_with_openai(prompt, "company")
        else:
            result = _rule_based_company_score(company_data, icp_profile)
        
        latency_ms = int((time.time() - start) * 1000)
        result["latency_ms"] = latency_ms
        
        return CompanyScoreResult(**result)
    
    async def _score_with_anthropic(self, prompt: str, entity_type: str) -> dict:
        schema = _get_score_schema(entity_type)
        
        message = await self.anthropic.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
            system=f"""You are a B2B lead scoring expert. Analyze the provided {entity_type} data 
and return a JSON object with scores from 0-100 for each dimension. Be precise and data-driven.
Always respond with valid JSON only, no markdown. Schema: {json.dumps(schema)}""",
        )
        
        content = message.content[0].text
        scores = json.loads(content)
        scores["model_used"] = "claude-haiku-4-5-20251001"
        scores["tokens_used"] = message.usage.input_tokens + message.usage.output_tokens
        return scores
    
    async def _score_with_openai(self, prompt: str, entity_type: str) -> dict:
        schema = _get_score_schema(entity_type)
        
        response = await self.openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"""You are a B2B lead scoring expert. 
Analyze the {entity_type} data and return scores 0-100 per dimension as JSON. Schema: {json.dumps(schema)}"""},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            max_tokens=1024,
        )
        
        scores = json.loads(response.choices[0].message.content)
        scores["model_used"] = "gpt-4o-mini"
        scores["tokens_used"] = response.usage.total_tokens
        return scores


def _build_contact_scoring_prompt(contact_data: dict, icp_profile: dict | None) -> str:
    lines = [
        "Score this B2B contact:",
        f"Name: {contact_data.get('first_name', '')} {contact_data.get('last_name', '')}",
        f"Title: {contact_data.get('designation', 'Unknown')}",
        f"Department: {contact_data.get('department', 'Unknown')}",
        f"Seniority: {contact_data.get('seniority', 'Unknown')}",
        f"Company: {contact_data.get('company_name', 'Unknown')}",
        f"Industry: {contact_data.get('company_industry', 'Unknown')}",
        f"Company Size: {contact_data.get('company_size', 'Unknown')} employees",
        f"Technologies: {', '.join(contact_data.get('technologies', []) or [])}",
        f"Email verified: {contact_data.get('email_verified', False)}",
        f"Has LinkedIn: {bool(contact_data.get('linkedin_url'))}",
    ]
    if icp_profile:
        lines.append(f"\nIdeal Customer Profile:")
        lines.append(f"Target industries: {', '.join(icp_profile.get('target_industries', [])[:5])}")
        lines.append(f"Target seniority: {', '.join(icp_profile.get('target_seniority', []))}")
        lines.append(f"Target company size: {icp_profile.get('target_company_size', 'Any')}")
        lines.append(f"Required technologies: {', '.join(icp_profile.get('required_technologies', [])[:5])}")
    return "\n".join(lines)


def _build_company_scoring_prompt(company_data: dict, icp_profile: dict | None) -> str:
    lines = [
        "Score this B2B company as a potential customer:",
        f"Name: {company_data.get('name', 'Unknown')}",
        f"Industry: {company_data.get('industry', 'Unknown')}",
        f"Employees: {company_data.get('employee_count', 'Unknown')}",
        f"Annual Revenue: ${company_data.get('annual_revenue', 0):,}" if company_data.get('annual_revenue') else "Annual Revenue: Unknown",
        f"Country: {company_data.get('country', 'Unknown')}",
        f"Technologies: {', '.join(company_data.get('technologies', []) or [])}",
        f"Description: {(company_data.get('description') or '')[:200]}",
    ]
    if icp_profile:
        lines.append(f"\nIdeal Customer Profile:")
        lines.append(f"Target industries: {', '.join(icp_profile.get('target_industries', [])[:5])}")
        lines.append(f"Target size: {icp_profile.get('target_company_size', 'Any')}")
        lines.append(f"Required tech: {', '.join(icp_profile.get('required_technologies', [])[:5])}")
        lines.append(f"Min revenue: ${icp_profile.get('min_annual_revenue', 0):,}")
    return "\n".join(lines)


def _get_score_schema(entity_type: str) -> dict:
    base = {
        "overall_score": "number 0-100, weighted average of all dimensions",
        "industry_score": "number 0-100, alignment with target industries",
        "technology_score": "number 0-100, relevant tech stack",
        "engagement_score": "number 0-100, data completeness and engagement signals",
        "fit_score": "number 0-100, overall ICP fit",
        "score_breakdown": {
            "reasoning": "string, 2-3 sentence explanation",
            "strengths": ["list of positive signals"],
            "weaknesses": ["list of negative signals or missing data"],
            "recommendation": "string: HOT | WARM | COLD | DISQUALIFIED"
        }
    }
    if entity_type == "contact":
        base["seniority_score"] = "number 0-100, seniority level match"
        base["company_score"] = "number 0-100, company size/industry match"
    else:
        base["company_score"] = "number 0-100, company size and revenue signals"
        base["seniority_score"] = "number, set to 0 for companies"
    return base


def _rule_based_contact_score(contact_data: dict, icp_profile: dict | None) -> dict:
    """Fallback rule-based scoring when no AI API keys configured."""
    seniority_map = {"C_LEVEL": 100, "VP": 85, "DIRECTOR": 70, "MANAGER": 55, "INDIVIDUAL": 30}
    seniority_score = seniority_map.get(contact_data.get("seniority", ""), 40)
    
    engagement_score = 40
    if contact_data.get("email"): engagement_score += 20
    if contact_data.get("phone"): engagement_score += 15
    if contact_data.get("linkedin_url"): engagement_score += 15
    if contact_data.get("email_verified"): engagement_score += 10
    
    industry_score = 60
    tech_score = 50
    fit_score = (seniority_score + engagement_score + industry_score) / 3
    overall = (seniority_score * 0.3 + engagement_score * 0.2 + industry_score * 0.2 + tech_score * 0.15 + fit_score * 0.15)
    
    return {
        "overall_score": round(overall, 1),
        "seniority_score": seniority_score,
        "engagement_score": engagement_score,
        "industry_score": industry_score,
        "technology_score": tech_score,
        "company_score": 50,
        "fit_score": round(fit_score, 1),
        "score_breakdown": {
            "reasoning": "Rule-based score (no AI API key configured).",
            "strengths": ["Has email"] if contact_data.get("email") else [],
            "weaknesses": ["No AI scoring configured"],
            "recommendation": "WARM" if overall >= 60 else "COLD"
        },
        "model_used": "rule_based",
        "tokens_used": 0,
    }


def _rule_based_company_score(company_data: dict, icp_profile: dict | None) -> dict:
    employee_count = company_data.get("employee_count") or 0
    size_score = min(100, (employee_count / 10000) * 100) if employee_count > 0 else 30
    
    revenue = company_data.get("annual_revenue") or 0
    revenue_score = min(100, (revenue / 100_000_000) * 100) if revenue > 0 else 30
    
    company_score = (size_score + revenue_score) / 2
    tech_score = min(100, len(company_data.get("technologies") or []) * 10)
    industry_score = 60
    engagement_score = 50 + (10 if company_data.get("description") else 0) + (10 if company_data.get("domain") else 0)
    fit_score = (company_score + industry_score) / 2
    overall = company_score * 0.3 + industry_score * 0.25 + tech_score * 0.2 + engagement_score * 0.15 + fit_score * 0.1
    
    return {
        "overall_score": round(overall, 1),
        "company_score": round(company_score, 1),
        "industry_score": industry_score,
        "technology_score": round(tech_score, 1),
        "engagement_score": engagement_score,
        "fit_score": round(fit_score, 1),
        "seniority_score": 0,
        "score_breakdown": {
            "reasoning": "Rule-based score (no AI API key configured).",
            "strengths": [f"{employee_count} employees"] if employee_count else [],
            "weaknesses": ["No AI scoring configured"],
            "recommendation": "WARM" if overall >= 60 else "COLD"
        },
        "model_used": "rule_based",
        "tokens_used": 0,
    }


_scorer_instance: AIScorer | None = None

def get_scorer() -> AIScorer:
    global _scorer_instance
    if _scorer_instance is None:
        _scorer_instance = AIScorer()
    return _scorer_instance
