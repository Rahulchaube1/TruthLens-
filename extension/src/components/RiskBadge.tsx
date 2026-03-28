import React from "react";

const LEVEL_STYLES: Record<string, string> = {
  low: "bg-green-700 text-green-100",
  medium: "bg-yellow-600 text-yellow-100",
  high: "bg-orange-600 text-orange-100",
  critical: "bg-red-700 text-red-100",
};

export default function RiskBadge({ level }: { level: string }) {
  const cls = LEVEL_STYLES[level] ?? "bg-gray-700 text-gray-100";
  return (
    <span className={`ml-auto text-xs font-semibold px-2 py-0.5 rounded-full uppercase ${cls}`}>
      {level}
    </span>
  );
}
