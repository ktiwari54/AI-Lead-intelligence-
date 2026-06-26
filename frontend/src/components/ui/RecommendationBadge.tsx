import clsx from "clsx";

type Recommendation = "HOT" | "WARM" | "COLD" | "DISQUALIFIED";

const styles: Record<Recommendation, string> = {
  HOT: "bg-red-100 text-red-700 border-red-200",
  WARM: "bg-orange-100 text-orange-700 border-orange-200",
  COLD: "bg-blue-100 text-blue-700 border-blue-200",
  DISQUALIFIED: "bg-gray-100 text-gray-600 border-gray-200",
};

const icons: Record<Recommendation, string> = {
  HOT: "🔥",
  WARM: "♨️",
  COLD: "❄️",
  DISQUALIFIED: "✗",
};

export function RecommendationBadge({ recommendation }: { recommendation: Recommendation }) {
  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full border text-xs font-semibold",
        styles[recommendation]
      )}
    >
      <span>{icons[recommendation]}</span>
      {recommendation}
    </span>
  );
}
