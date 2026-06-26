"use client";
import { RadialBarChart, RadialBar, PolarAngleAxis } from "recharts";

interface Props {
  score: number;
  label?: string;
  size?: number;
}

function scoreColor(score: number): string {
  if (score >= 80) return "#10b981";
  if (score >= 60) return "#22c55e";
  if (score >= 40) return "#eab308";
  if (score >= 20) return "#f97316";
  return "#ef4444";
}

export function ScoreGauge({ score, label, size = 120 }: Props) {
  const color = scoreColor(score);
  const data = [{ value: score, fill: color }];

  return (
    <div className="flex flex-col items-center">
      <div className="relative" style={{ width: size, height: size }}>
        <RadialBarChart
          width={size}
          height={size}
          cx={size / 2}
          cy={size / 2}
          innerRadius={size * 0.35}
          outerRadius={size * 0.48}
          barSize={size * 0.12}
          data={data}
          startAngle={90}
          endAngle={-270}
        >
          <PolarAngleAxis type="number" domain={[0, 100]} angleAxisId={0} tick={false} />
          <RadialBar background dataKey="value" cornerRadius={size * 0.06} angleAxisId={0} />
        </RadialBarChart>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-2xl font-bold" style={{ color }}>
            {Math.round(score)}
          </span>
          <span className="text-xs text-gray-500">/ 100</span>
        </div>
      </div>
      {label && <p className="mt-1 text-sm font-medium text-gray-600">{label}</p>}
    </div>
  );
}
