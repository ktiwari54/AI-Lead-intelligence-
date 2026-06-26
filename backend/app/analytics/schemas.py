from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel


class TimeSeriesPoint(BaseModel):
    date: str
    value: int | float
    label: str | None = None


class BreakdownItem(BaseModel):
    label: str
    value: int | float
    percentage: float | None = None
    color: str | None = None


class DashboardStats(BaseModel):
    total_companies: int
    total_contacts: int
    total_searches: int
    ai_scores_generated: int
    credits_remaining: int
    credits_monthly: int
    active_deals: int
    new_companies_this_month: int
    new_contacts_this_month: int
    avg_lead_score: float | None


class LeadVelocityData(BaseModel):
    companies: list[TimeSeriesPoint]
    contacts: list[TimeSeriesPoint]
    period_days: int


class ScoreDistribution(BaseModel):
    buckets: list[BreakdownItem]
    avg_score: float
    median_score: float
    total_scored: int


class IndustryBreakdown(BaseModel):
    companies_by_industry: list[BreakdownItem]
    contacts_by_industry: list[BreakdownItem]


class GeographyBreakdown(BaseModel):
    companies_by_country: list[BreakdownItem]
    contacts_by_country: list[BreakdownItem]


class SeniorityBreakdown(BaseModel):
    contacts_by_seniority: list[BreakdownItem]


class SearchActivityData(BaseModel):
    searches_over_time: list[TimeSeriesPoint]
    top_queries: list[BreakdownItem]
    total_searches: int
    avg_results_per_search: float


class CRMFunnelData(BaseModel):
    stages: list[BreakdownItem]
    total_deals: int
    total_value: float
    avg_deal_value: float
    deals_by_status: list[BreakdownItem]


class CreditUsageData(BaseModel):
    usage_over_time: list[TimeSeriesPoint]
    usage_by_type: list[BreakdownItem]
    total_used_this_month: int
    total_remaining: int


class FullAnalyticsResponse(BaseModel):
    dashboard_stats: DashboardStats
    lead_velocity: LeadVelocityData
    score_distribution: ScoreDistribution
    industry_breakdown: IndustryBreakdown
    geography: GeographyBreakdown
    seniority: SeniorityBreakdown
    search_activity: SearchActivityData
    crm_funnel: CRMFunnelData
    credit_usage: CreditUsageData
    generated_at: datetime
