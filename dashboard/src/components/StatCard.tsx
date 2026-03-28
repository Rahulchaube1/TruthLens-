
interface Props {
  title: string;
  value: string | number;
  subtitle?: string;
  accent?: "blue" | "red" | "green" | "yellow";
}

const ACCENT_MAP: Record<string, string> = {
  blue: "border-blue-500",
  red: "border-red-500",
  green: "border-green-500",
  yellow: "border-yellow-500",
};

export default function StatCard({ title, value, subtitle, accent = "blue" }: Props) {
  return (
    <div className={`bg-gray-900 border-l-4 ${ACCENT_MAP[accent]} rounded-lg p-5`}>
      <p className="text-sm text-gray-400">{title}</p>
      <p className="text-3xl font-bold mt-1">{value}</p>
      {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
    </div>
  );
}
