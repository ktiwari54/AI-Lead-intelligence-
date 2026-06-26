"use client";

import { useState } from "react";
import { ScoreGauge } from "@/components/ui/ScoreGauge";
import { RecommendationBadge } from "@/components/ui/RecommendationBadge";
import {
  useContactScores,
  useCompanyScores,
  useScoreContact,
  useScoreCompany,
  LeadScore,
} from "@/hooks/useAI";

type Tab = "contact" | "company";

const SUB_GAUGES: { key: keyof LeadScore; label: string }[] = [
  { key: "seniority_score", label: "Seniority" },
  { key: "company_score", label: "Company" },
  { key: "engagement_score", label: "Engagement" },
  { key: "technology_score", label: "Technology" },
  { key: "industry_score", label: "Industry" },
  { key: "fit_score", label: "Fit" },
];

function Alert({ message, type }: { message: string; type: "success" | "error" }) {
  return (
    <div
      className={`rounded-lg px-4 py-3 text-sm font-medium border ${
        type === "success"
          ? "bg-green-50 text-green-700 border-green-200"
          : "bg-red-50 text-red-700 border-red-200"
      }`}
    >
      {message}
    </div>
  );
}

function ScoreResults({ score }: { score: LeadScore }) {
  const breakdown = score.score_breakdown;
  return (
    <div className="space-y-6">
      {/* Overall gauge */}
      <div className="flex flex-col items-center py-4">
        <ScoreGauge score={score.overall_score} label="Overall Score" size={160} />
        <div className="mt-3">
          <RecommendationBadge recommendation={breakdown.recommendation} />
        </div>
      </div>

      {/* Sub-gauges */}
      <div className="grid grid-cols-3 gap-4">
        {SUB_GAUGES.map(({ key, label }) => (
          <div key={key} className="flex justify-center">
            <ScoreGauge score={score[key] as number} label={label} size={90} />
          </div>
        ))}
      </div>

      {/* Reasoning */}
      {breakdown.reasoning && (
        <div className="bg-gray-50 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-gray-700 mb-1">Reasoning</h3>
          <p className="text-sm text-gray-600">{breakdown.reasoning}</p>
        </div>
      )}

      {/* Strengths & Weaknesses */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <h3 className="text-sm font-semibold text-gray-700 mb-2">Strengths</h3>
          <ul className="space-y-1">
            {breakdown.strengths?.map((s, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-gray-600">
                <span className="text-green-500 font-bold mt-0.5">✓</span>
                {s}
              </li>
            ))}
          </ul>
        </div>
        <div>
          <h3 className="text-sm font-semibold text-gray-700 mb-2">Weaknesses</h3>
          <ul className="space-y-1">
            {breakdown.weaknesses?.map((w, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-gray-600">
                <span className="text-red-500 font-bold mt-0.5">✗</span>
                {w}
              </li>
            ))}
          </ul>
        </div>
      </div>

      <p className="text-xs text-gray-400">Model used: {score.model_used}</p>
    </div>
  );
}

function ScoringPanel({ type }: { type: "contact" | "company" }) {
  const [id, setId] = useState("");
  const [icpText, setIcpText] = useState("");
  const [alert, setAlert] = useState<{ message: string; kind: "success" | "error" } | null>(null);
  const [submittedId, setSubmittedId] = useState("");

  const contactScores = useContactScores(type === "contact" ? submittedId : "");
  const companyScores = useCompanyScores(type === "company" ? submittedId : "");
  const scores = type === "contact" ? contactScores : companyScores;

  const scoreContact = useScoreContact();
  const scoreCompany = useScoreCompany();
  const mutation = type === "contact" ? scoreContact : scoreCompany;

  const handleSubmit = async () => {
    if (!id.trim()) return;
    let icpProfile: object | undefined;
    if (icpText.trim()) {
      try {
        icpProfile = JSON.parse(icpText);
      } catch {
        setAlert({ message: "Invalid JSON in ICP Profile field.", kind: "error" });
        return;
      }
    }

    setAlert(null);
    try {
      if (type === "contact") {
        const res: any = await scoreContact.mutateAsync({ contactId: id.trim(), icpProfile });
        const s = res?.data?.overall_score ?? res?.overall_score;
        setAlert({ message: `Scoring complete! Score: ${s}/100`, kind: "success" });
      } else {
        const res: any = await scoreCompany.mutateAsync({ companyId: id.trim(), icpProfile });
        const s = res?.data?.overall_score ?? res?.overall_score;
        setAlert({ message: `Scoring complete! Score: ${s}/100`, kind: "success" });
      }
      setSubmittedId(id.trim());
    } catch {
      setAlert({ message: "Scoring failed. Please try again.", kind: "error" });
    }
  };

  const latestScore = scores.data?.[0];

  return (
    <div className="space-y-5">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {type === "contact" ? "Contact ID" : "Company ID"} (UUID)
        </label>
        <input
          type="text"
          value={id}
          onChange={(e) => setId(e.target.value)}
          placeholder={`Enter ${type} UUID...`}
          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          ICP Profile (optional JSON)
        </label>
        <textarea
          value={icpText}
          onChange={(e) => setIcpText(e.target.value)}
          rows={4}
          placeholder='{"industry": "SaaS", "min_employees": 50}'
          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
      </div>

      <button
        onClick={handleSubmit}
        disabled={mutation.isPending || !id.trim()}
        className="px-5 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {mutation.isPending ? "Scoring..." : `Score ${type === "contact" ? "Contact" : "Company"}`}
      </button>

      {alert && <Alert message={alert.message} type={alert.kind} />}

      {scores.isLoading && submittedId && (
        <div className="animate-pulse space-y-3 pt-4">
          <div className="h-40 bg-gray-100 rounded-xl" />
          <div className="h-24 bg-gray-100 rounded-xl" />
        </div>
      )}

      {latestScore && !scores.isLoading && (
        <div className="border-t border-gray-100 pt-6">
          <ScoreResults score={latestScore} />
        </div>
      )}
    </div>
  );
}

export default function AIScoringPage() {
  const [tab, setTab] = useState<Tab>("contact");

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">AI Scoring</h1>

      {/* Tabs */}
      <div className="flex border-b border-gray-200 mb-6">
        {(["contact", "company"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-5 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors capitalize ${
              tab === t
                ? "border-indigo-600 text-indigo-600"
                : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            Score {t === "contact" ? "Contact" : "Company"}
          </button>
        ))}
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <ScoringPanel type={tab} />
      </div>
    </div>
  );
}
