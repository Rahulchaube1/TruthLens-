import { useMemo } from "react";
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from "recharts";
import { useStore } from "../store/useStore";
import StatCard from "../components/StatCard";

const COLORS = ["#3b82f6", "#ef4444", "#22c55e", "#f59e0b"];

export default function Analytics() {
  const { scans } = useStore();

  const typeBreakdown = useMemo(() => {
    const counts: Record<string, number> = { video: 0, audio: 0, image: 0 };
    scans.forEach((s) => { counts[s.scan_type] = (counts[s.scan_type] ?? 0) + 1; });
    return Object.entries(counts).map(([name, value]) => ({ name, value }));
  }, [scans]);

  const riskBreakdown = useMemo(() => {
    const counts: Record<string, number> = { low: 0, medium: 0, high: 0, critical: 0 };
    scans.forEach((s) => { counts[s.risk_level] = (counts[s.risk_level] ?? 0) + 1; });
    return Object.entries(counts).map(([name, value]) => ({ name, value }));
  }, [scans]);

  const confidenceOverTime = useMemo(() => {
    return scans
      .slice()
      .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
      .map((s, i) => ({
        index: i + 1,
        confidence: Math.round(s.confidence * 100),
        type: s.scan_type,
      }));
  }, [scans]);

  const fakeRate = scans.length
    ? Math.round((scans.filter((s) => s.is_fake).length / scans.length) * 100)
    : 0;

  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-bold">Analytics</h1>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard title="Total Scans" value={scans.length} accent="blue" />
        <StatCard title="Fake Detection Rate" value={`${fakeRate}%`} accent="red" />
        <StatCard
          title="Most Scanned Type"
          value={typeBreakdown.reduce((a, b) => (a.value > b.value ? a : b), { name: "—", value: 0 }).name}
          accent="green"
        />
      </div>

      {scans.length === 0 ? (
        <div className="bg-gray-900 rounded-xl p-12 text-center text-gray-500">
          No scan data yet. Start scanning to see analytics.
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Scan type breakdown */}
          <div className="bg-gray-900 rounded-xl p-6">
            <h2 className="text-lg font-semibold mb-4">Scans by Type</h2>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={typeBreakdown}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="name" stroke="#9ca3af" />
                <YAxis stroke="#9ca3af" />
                <Tooltip contentStyle={{ backgroundColor: "#1f2937", border: "none" }} />
                <Bar dataKey="value" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Risk level pie */}
          <div className="bg-gray-900 rounded-xl p-6">
            <h2 className="text-lg font-semibold mb-4">Risk Level Distribution</h2>
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie data={riskBreakdown} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label>
                  {riskBreakdown.map((_entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: "#1f2937", border: "none" }} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Confidence over time */}
          <div className="bg-gray-900 rounded-xl p-6 lg:col-span-2">
            <h2 className="text-lg font-semibold mb-4">Confidence Score Over Time</h2>
            <ResponsiveContainer width="100%" height={240}>
              <LineChart data={confidenceOverTime}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="index" stroke="#9ca3af" label={{ value: "Scan #", position: "insideBottom", fill: "#9ca3af" }} />
                <YAxis stroke="#9ca3af" domain={[0, 100]} unit="%" />
                <Tooltip contentStyle={{ backgroundColor: "#1f2937", border: "none" }} />
                <Line type="monotone" dataKey="confidence" stroke="#3b82f6" dot={false} strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
}
