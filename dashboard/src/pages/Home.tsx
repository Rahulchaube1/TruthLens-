import { useState } from "react";
import { useStore } from "../store/useStore";
import { detectApi } from "../api/client";
import StatCard from "../components/StatCard";
import RiskBadge from "../components/RiskBadge";

export default function Home() {
  const { scans, addScan, isLoading, setLoading, auth } = useStore();
  const [url, setUrl] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [lastResult, setLastResult] = useState<Record<string, unknown> | null>(null);

  const recentScans = scans.slice(0, 5);
  const fakeCount = scans.filter((s) => s.is_fake).length;
  const avgConf = scans.length
    ? Math.round((scans.reduce((acc, s) => acc + s.confidence, 0) / scans.length) * 100)
    : 0;

  const handleScan = async () => {
    if (!url) return;
    setError(null);
    setLoading(true);
    try {
      const res = await detectApi.detectVideo({ url });
      const data = res.data;
      const record = {
        id: crypto.randomUUID(),
        user_id: auth.userId ?? "anon",
        scan_type: "video" as const,
        is_fake: data.is_deepfake,
        confidence: data.confidence,
        risk_level: data.risk_level,
        timestamp: new Date().toISOString(),
        source_url: url,
      };
      addScan(record);
      setLastResult(data as unknown as Record<string, unknown>);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Scan failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Hero */}
      <div>
        <h1 className="text-3xl font-bold">TruthLens Dashboard</h1>
        <p className="text-gray-400 mt-1">Real-time deepfake & media authenticity detection</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard title="Total Scans" value={scans.length} accent="blue" />
        <StatCard title="Deepfakes Detected" value={fakeCount} accent="red" />
        <StatCard title="Avg Confidence" value={`${avgConf}%`} accent="green" />
      </div>

      {/* Quick scan */}
      <div className="bg-gray-900 rounded-xl p-6">
        <h2 className="text-lg font-semibold mb-4">Quick Scan</h2>
        <div className="flex gap-3">
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="Paste video URL to scan…"
            className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-sm outline-none focus:border-blue-500 transition-colors"
          />
          <button
            onClick={handleScan}
            disabled={isLoading || !url}
            className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 px-5 py-2 rounded-lg text-sm font-medium transition-colors"
          >
            {isLoading ? "Scanning…" : "Scan"}
          </button>
        </div>
        {error && <p className="text-red-400 text-sm mt-2">{error}</p>}
        {lastResult && (
          <div className="mt-4 p-4 bg-gray-800 rounded-lg text-sm space-y-2">
            <div className="flex items-center gap-2">
              <span className="font-medium">Result:</span>
              <span className={(lastResult.is_deepfake as boolean) ? "text-red-400" : "text-green-400"}>
                {(lastResult.is_deepfake as boolean) ? "⚠ Deepfake Detected" : "✓ Appears Authentic"}
              </span>
            </div>
            <div className="text-gray-400">
              Confidence: {Math.round((lastResult.confidence as number) * 100)}% •
              Risk: <RiskBadge level={lastResult.risk_level as string} />
            </div>
          </div>
        )}
      </div>

      {/* Recent scans */}
      {recentScans.length > 0 && (
        <div className="bg-gray-900 rounded-xl p-6">
          <h2 className="text-lg font-semibold mb-4">Recent Scans</h2>
          <div className="space-y-2">
            {recentScans.map((scan) => (
              <div key={scan.id} className="flex items-center justify-between py-2 border-b border-gray-800 last:border-0">
                <div>
                  <span className="text-sm capitalize">{scan.scan_type}</span>
                  {scan.source_url && (
                    <p className="text-xs text-gray-500 truncate max-w-xs">{scan.source_url}</p>
                  )}
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-sm text-gray-400">{Math.round(scan.confidence * 100)}%</span>
                  <RiskBadge level={scan.risk_level} />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
