from __future__ import annotations

from typing import Any


class AIInsightEngine:
    """Generates natural-language insights from analytics snapshots (stub for LLM integration)."""

    def summarize_dashboard(self, snapshot: dict[str, Any], kpis: list[dict[str, Any]]) -> dict[str, Any]:
        companies = snapshot.get("total_companies", 0)
        contacts = snapshot.get("total_contacts", 0)
        pipeline = snapshot.get("pipeline_value", 0)
        score = snapshot.get("avg_lead_score")
        growth_items = [k for k in kpis if k.get("growth_rate") and k["growth_rate"] > 0]

        summary = (
            f"Your organization has {companies:,} companies and {contacts:,} contacts "
            f"with ${pipeline:,.0f} in open pipeline value."
        )
        if score:
            summary += f" Average lead score is {score:.1f}."
        if growth_items:
            top = max(growth_items, key=lambda k: k.get("growth_rate", 0))
            summary += f" Strongest growth in {top.get('label', top['metric_key'])} ({top['growth_rate']:+.1f}%)."

        recommendations = []
        if snapshot.get("verification_rate", 100) < 50:
            recommendations.append("Run email verification workflow to improve contact data quality.")
        if score and score < 60:
            recommendations.append("Trigger AI lead scoring on new contacts to improve qualification.")
        if pipeline > 0 and contacts > 0 and contacts / max(companies, 1) < 2:
            recommendations.append("Enrich companies with additional contacts to expand pipeline coverage.")

        return {
            "summary": summary,
            "recommendations": recommendations,
            "highlights": [
                {"type": "kpi", "label": k.get("label"), "value": k.get("current_value"), "status": k.get("status")}
                for k in kpis[:5]
            ],
            "stub": True,
        }

    def answer_question(self, question: str, context: dict[str, Any]) -> dict[str, Any]:
        q = question.lower()
        snapshot = context.get("snapshot", {})
        if "pipeline" in q:
            answer = f"Open pipeline value is ${snapshot.get('pipeline_value', 0):,.0f}."
        elif "contact" in q:
            answer = f"You have {snapshot.get('total_contacts', 0):,} contacts ({snapshot.get('verified_contacts', 0):,} verified)."
        elif "score" in q or "lead" in q:
            answer = f"Average lead score is {snapshot.get('avg_lead_score', 'N/A')}."
        else:
            answer = "I can help summarize dashboards, explain KPIs, compare periods, and recommend actions. Try asking about pipeline, contacts, or lead scores."

        return {"question": question, "answer": answer, "sources": ["metrics_snapshot"], "stub": True}