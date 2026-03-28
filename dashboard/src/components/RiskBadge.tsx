
const STYLES: Record<string, string> = {
  low: "bg-green-900 text-green-300",
  medium: "bg-yellow-900 text-yellow-300",
  high: "bg-orange-900 text-orange-300",
  critical: "bg-red-900 text-red-300",
};

export default function RiskBadge({ level }: { level: string }) {
  return (
    <span className={`text-xs font-semibold px-2 py-0.5 rounded-full uppercase ${STYLES[level] ?? "bg-gray-800 text-gray-300"}`}>
      {level}
    </span>
  );
}
