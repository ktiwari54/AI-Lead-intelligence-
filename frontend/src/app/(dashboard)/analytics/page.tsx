"use client";

import { useState } from "react";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import {
  useDashboardStats,
  useLeadVelocity,
  useScoreDistribution,
  useCRMFunnel,
  useIndustryBreakdown,
} from "@/hooks/useAnalytics";
import { PageHeader } from "@/components/enterprise/PageHeader";

const PERIOD_OPTIONS = [
  { label: "7d", value: 7 },
  { label: "30d", value: 30 },
  { label: "90d", value: 90 },
];

const PIE_COLORS = [
  "#6366f1", "#22c55e", "#f59e0b", "#ef4444", "#3b82f6",
  "#8b5cf6", "#ec4899", "#14b8a6", "#f97316", "#84cc16",
];

function StatCard({
  label,
  value,
  loading,
}: {
  label: string;
  value: string | number | null;
  loading?: boolean;
}) {
  if (loading) {
    return (
      <div className="bg-card rounded-xl border border-border p-6 animate-pulse">
        <div className="h-4 bg-muted rounded w-3/4 mb-3" />
        <div className="h-8 bg-muted rounded w-1/2" />
      </div>
    );
  }
  return (
    <div className="bg-card rounded-xl border border-border p-6">
      <p className="text-sm text-muted-foreground font-medium">{label}</p>
      <p className="text-3xl font-bold text-foreground mt-1">
        {value === null || value === undefined ? "—" : value}
      </p>
    </div>
  );
}

function SectionSkeleton({ height = 280 }: { height?: number }) {
  return (
    <div
      className="bg-card rounded-xl border border-border animate-pulse"
      style={{ height }}
    />
  );
}

export default function AnalyticsPage() {
  const [period, setPeriod] = useState(30);

  const stats = useDashboardStats();
  const velocity = useLeadVelocity(period);
  const scoreDist = useScoreDistribution();
  const funnel = useCRMFunnel();
  const industry = useIndustryBreakdown();

  const hasError =
    stats.isError || velocity.isError || scoreDist.isError || funnel.isError || industry.isError;

  const refetchAll = () => {
    stats.refetch();
    velocity.refetch();
    scoreDist.refetch();
    funnel.refetch();
    industry.refetch();
  };

  return (
    <div className="page-container mx-auto max-w-7xl space-y-6">
      <PageHeader
        title="Analytics Reports"
        description={`Performance insights across discovery, scoring, and CRM. Last updated: ${new Date().toLocaleString()}`}
        actions={
          <div className="flex items-center gap-2">
            {PERIOD_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                onClick={() => setPeriod(opt.value)}
                className={`rounded-lg border px-4 py-1.5 text-sm font-medium transition-colors ${
                  period === opt.value
                    ? "border-primary bg-primary text-primary-foreground"
                    : "border-border bg-card text-muted-foreground hover:border-primary/50"
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        }
      />

      {hasError && (
        <div className="bg-destructive/5 border border-destructive/20 rounded-xl p-4 flex items-center justify-between">
          <span className="text-destructive text-sm font-medium">
            Failed to load analytics data.
          </span>
          <button
            onClick={refetchAll}
            className="text-sm font-medium text-destructive hover:underline"
          >
            Retry
          </button>
        </div>
      )}

      {/* Row 1: Stat Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          label="Total Companies"
          value={stats.data?.total_companies ?? null}
          loading={stats.isLoading}
        />
        <StatCard
          label="Total Contacts"
          value={stats.data?.total_contacts ?? null}
          loading={stats.isLoading}
        />
        <StatCard
          label="AI Scores Generated"
          value={stats.data?.ai_scores_generated ?? null}
          loading={stats.isLoading}
        />
        <StatCard
          label="Avg Lead Score"
          value={
            stats.data?.avg_lead_score !== null && stats.data?.avg_lead_score !== undefined
              ? Number(stats.data.avg_lead_score).toFixed(1)
              : null
          }
          loading={stats.isLoading}
        />
      </div>

      {/* Row 2: Lead Velocity */}
      <div className="bg-card rounded-xl border border-border p-6">
        <h2 className="text-base font-semibold text-foreground mb-4">Lead Velocity</h2>
        {velocity.isLoading ? (
          <SectionSkeleton height={280} />
        ) : velocity.data ? (
          <ResponsiveContainer width="100%" height={280}>
            <LineChart
              data={velocity.data.companies.map((c, i) => ({
                date: c.date,
                companies: c.value,
                contacts: velocity.data!.contacts[i]?.value ?? 0,
              }))}
              margin={{ top: 5, right: 20, left: 0, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="date" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="companies"
                stroke="#6366f1"
                strokeWidth={2}
                dot={false}
                name="Companies"
              />
              <Line
                type="monotone"
                dataKey="contacts"
                stroke="#22c55e"
                strokeWidth={2}
                dot={false}
                name="Contacts"
              />
            </LineChart>
          </ResponsiveContainer>
        ) : null}
      </div>

      {/* Row 3: Score Distribution + CRM Funnel */}
      <div className="grid grid-cols-5 gap-4">
        {/* Score Distribution (60%) */}
        <div className="col-span-3 bg-card rounded-xl border border-border p-6">
          <h2 className="text-base font-semibold text-foreground mb-4">Score Distribution</h2>
          {scoreDist.isLoading ? (
            <SectionSkeleton height={280} />
          ) : scoreDist.data ? (
            <>
              <div className="flex gap-4 mb-3 text-sm text-muted-foreground">
                <span>Avg: <strong className="text-foreground">{scoreDist.data.avg_score?.toFixed(1)}</strong></span>
                <span>Median: <strong className="text-foreground">{scoreDist.data.median_score?.toFixed(1)}</strong></span>
                <span>Scored: <strong className="text-foreground">{scoreDist.data.total_scored}</strong></span>
              </div>
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={scoreDist.data.buckets} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Bar dataKey="value" name="Count" radius={[4, 4, 0, 0]}>
                    {scoreDist.data.buckets.map((bucket, idx) => (
                      <Cell key={idx} fill={bucket.color ?? PIE_COLORS[idx % PIE_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </>
          ) : null}
        </div>

        {/* CRM Funnel (40%) */}
        <div className="col-span-2 bg-card rounded-xl border border-border p-6">
          <h2 className="text-base font-semibold text-foreground mb-4">CRM Funnel</h2>
          {funnel.isLoading ? (
            <SectionSkeleton height={280} />
          ) : funnel.data ? (
            <>
              <div className="flex gap-4 mb-3 text-sm text-muted-foreground">
                <span>Deals: <strong className="text-foreground">{funnel.data.total_deals}</strong></span>
                <span>Avg: <strong className="text-foreground">${funnel.data.avg_deal_value?.toLocaleString()}</strong></span>
              </div>
              <ResponsiveContainer width="100%" height={240}>
                <BarChart
                  layout="vertical"
                  data={funnel.data.stages}
                  margin={{ top: 5, right: 10, left: 10, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" horizontal={false} />
                  <XAxis type="number" tick={{ fontSize: 11 }} />
                  <YAxis type="category" dataKey="label" tick={{ fontSize: 11 }} width={80} />
                  <Tooltip />
                  <Bar dataKey="value" name="Deals" fill="#6366f1" radius={[0, 4, 4, 0]}>
                    {funnel.data.stages.map((_, idx) => (
                      <Cell key={idx} fill={PIE_COLORS[idx % PIE_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </>
          ) : null}
        </div>
      </div>

      {/* Row 4: Industry Breakdown */}
      <div className="grid grid-cols-2 gap-4">
        {/* Companies by Industry */}
        <div className="bg-card rounded-xl border border-border p-6">
          <h2 className="text-base font-semibold text-foreground mb-4">Companies by Industry</h2>
          {industry.isLoading ? (
            <SectionSkeleton height={260} />
          ) : industry.data ? (
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie
                  data={industry.data.companies_by_industry}
                  dataKey="value"
                  nameKey="label"
                  cx="50%"
                  cy="50%"
                  outerRadius={90}
                  label={({ label, percentage }) =>
                    percentage != null ? `${label} (${percentage.toFixed(0)}%)` : label
                  }
                  labelLine={false}
                >
                  {industry.data.companies_by_industry.map((_, idx) => (
                    <Cell key={idx} fill={PIE_COLORS[idx % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          ) : null}
        </div>

        {/* Contacts by Industry */}
        <div className="bg-card rounded-xl border border-border p-6">
          <h2 className="text-base font-semibold text-foreground mb-4">Contacts by Industry</h2>
          {industry.isLoading ? (
            <SectionSkeleton height={260} />
          ) : industry.data ? (
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie
                  data={industry.data.contacts_by_industry}
                  dataKey="value"
                  nameKey="label"
                  cx="50%"
                  cy="50%"
                  outerRadius={90}
                  label={({ label, percentage }) =>
                    percentage != null ? `${label} (${percentage.toFixed(0)}%)` : label
                  }
                  labelLine={false}
                >
                  {industry.data.contacts_by_industry.map((_, idx) => (
                    <Cell key={idx} fill={PIE_COLORS[idx % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          ) : null}
        </div>
      </div>
    </div>
  );
}
