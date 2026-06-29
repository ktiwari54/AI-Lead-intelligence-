from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


def _run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@shared_task(name="analytics.aggregate_daily_metrics")
def aggregate_daily_metrics():
    """Roll up daily metric aggregations for all organizations."""
    logger.info("Running daily analytics aggregation")

    async def _aggregate():
        from sqlalchemy import select
        from backend.database import AsyncSessionLocal
        from backend.app.organizations.models import Organization
        from backend.app.analytics.engines import MetricsEngine
        from backend.app.analytics.models import MetricAggregation

        engine = MetricsEngine()
        period_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

        async with AsyncSessionLocal() as db:
            orgs = (await db.execute(select(Organization.id))).scalars().all()
            metric_keys = [
                "companies_created", "contacts_created", "searches",
                "discovery_jobs", "ai_scores_generated",
            ]
            for org_id in orgs:
                snapshot = await engine.compute_snapshot(db, org_id)
                for key in metric_keys:
                    value = float(snapshot.get(key, 0) or 0)
                    existing = await db.execute(
                        select(MetricAggregation).where(
                            MetricAggregation.organization_id == org_id,
                            MetricAggregation.metric_key == key,
                            MetricAggregation.granularity == "daily",
                            MetricAggregation.period_start == period_start,
                        )
                    )
                    agg = existing.scalar_one_or_none()
                    if agg:
                        agg.value = value
                        agg.sample_count = 1
                    else:
                        db.add(MetricAggregation(
                            organization_id=org_id,
                            metric_key=key,
                            granularity="daily",
                            period_start=period_start,
                            value=value,
                            sample_count=1,
                        ))
            await db.commit()

    try:
        _run_async(_aggregate())
        return {"status": "completed"}
    except Exception as exc:
        logger.exception("Daily aggregation failed: %s", exc)
        raise


@shared_task(name="analytics.check_alert_rules")
def check_alert_rules():
    """Evaluate active alert rules and create alerts when thresholds are breached."""
    logger.info("Checking analytics alert rules")

    async def _check():
        from sqlalchemy import select
        from backend.database import AsyncSessionLocal
        from backend.app.analytics.models import Alert, AlertRule
        from backend.app.analytics.engines import MetricsEngine

        engine = MetricsEngine()
        async with AsyncSessionLocal() as db:
            rules = (await db.execute(
                select(AlertRule).where(
                    AlertRule.is_active == True,  # noqa: E712
                    AlertRule.deleted_at.is_(None),
                )
            )).scalars().all()

            for rule in rules:
                snapshot = await engine.compute_snapshot(db, rule.organization_id)
                current = float(snapshot.get(rule.metric_key, 0) or 0)
                threshold = float(rule.threshold)
                breached = False
                if rule.condition == "lt" and current < threshold:
                    breached = True
                elif rule.condition == "gt" and current > threshold:
                    breached = True
                elif rule.condition == "lte" and current <= threshold:
                    breached = True
                elif rule.condition == "gte" and current >= threshold:
                    breached = True

                if not breached:
                    continue

                cooldown = timedelta(minutes=rule.cooldown_minutes)
                recent = (await db.execute(
                    select(Alert).where(
                        Alert.rule_id == rule.id,
                        Alert.created_at >= datetime.now(timezone.utc) - cooldown,
                    ).limit(1)
                )).scalar_one_or_none()
                if recent:
                    continue

                db.add(Alert(
                    organization_id=rule.organization_id,
                    rule_id=rule.id,
                    title=f"Alert: {rule.name}",
                    message=f"{rule.metric_key} is {current} (threshold: {rule.condition} {threshold})",
                    severity=rule.severity,
                    metric_key=rule.metric_key,
                    current_value=current,
                ))
            await db.commit()

    try:
        _run_async(_check())
        return {"status": "completed"}
    except Exception as exc:
        logger.exception("Alert rule check failed: %s", exc)
        raise


@shared_task(name="analytics.refresh_forecasts")
def refresh_forecasts():
    """Refresh forecast results for active forecast models."""
    logger.info("Refreshing analytics forecasts")

    async def _refresh():
        from sqlalchemy import select
        from backend.database import AsyncSessionLocal
        from backend.app.analytics.models import ForecastModel, ForecastResult
        from backend.app.analytics.engines import ForecastEngine, MetricsEngine

        metrics_engine = MetricsEngine()
        forecast_engine = ForecastEngine()

        async with AsyncSessionLocal() as db:
            models = (await db.execute(
                select(ForecastModel).where(
                    ForecastModel.is_active == True,  # noqa: E712
                    ForecastModel.deleted_at.is_(None),
                )
            )).scalars().all()

            for model in models:
                series = await metrics_engine.time_series(
                    db, model.organization_id, model.metric_key, days=90
                )
                forecast = forecast_engine.forecast_metric(model.metric_key, series, periods=30)
                for point in forecast.get("forecasts", []):
                    fdate = datetime.fromisoformat(point["date"]).replace(tzinfo=timezone.utc)
                    existing = await db.execute(
                        select(ForecastResult).where(
                            ForecastResult.model_id == model.id,
                            ForecastResult.forecast_date == fdate,
                        )
                    )
                    result = existing.scalar_one_or_none()
                    if result:
                        result.predicted_value = point["predicted_value"]
                        result.lower_bound = point.get("lower_bound")
                        result.upper_bound = point.get("upper_bound")
                    else:
                        db.add(ForecastResult(
                            model_id=model.id,
                            organization_id=model.organization_id,
                            forecast_date=fdate,
                            predicted_value=point["predicted_value"],
                            lower_bound=point.get("lower_bound"),
                            upper_bound=point.get("upper_bound"),
                            confidence=point.get("confidence"),
                        ))
            await db.commit()

    try:
        _run_async(_refresh())
        return {"status": "completed"}
    except Exception as exc:
        logger.exception("Forecast refresh failed: %s", exc)
        raise