import { useEffect } from "react";
import { useStore } from "../store/useStore";
import { historyApi } from "../api/client";
import RiskBadge from "../components/RiskBadge";

export default function History() {
  const { scans, setScans, auth } = useStore();

  useEffect(() => {
    if (auth.token) {
      historyApi.getHistory(100).then((res) => setScans(res.data)).catch(() => {});
    }
  }, [auth.token, setScans]);

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Scan History</h1>

      {scans.length === 0 ? (
        <div className="bg-gray-900 rounded-xl p-12 text-center text-gray-500">
          No scans yet. Start scanning from the Home page or use the Chrome extension.
        </div>
      ) : (
        <div className="bg-gray-900 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-800 text-gray-400 text-left">
              <tr>
                <th className="px-4 py-3">Type</th>
                <th className="px-4 py-3">Result</th>
                <th className="px-4 py-3">Confidence</th>
                <th className="px-4 py-3">Risk</th>
                <th className="px-4 py-3">Time</th>
                <th className="px-4 py-3">Source</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {scans.map((scan) => (
                <tr key={scan.id} className="hover:bg-gray-800/50 transition-colors">
                  <td className="px-4 py-3 capitalize">{scan.scan_type}</td>
                  <td className={`px-4 py-3 font-medium ${scan.is_fake ? "text-red-400" : "text-green-400"}`}>
                    {scan.is_fake ? "Fake" : "Real"}
                  </td>
                  <td className="px-4 py-3 text-gray-300">{Math.round(scan.confidence * 100)}%</td>
                  <td className="px-4 py-3"><RiskBadge level={scan.risk_level} /></td>
                  <td className="px-4 py-3 text-gray-400">
                    {new Date(scan.timestamp).toLocaleString()}
                  </td>
                  <td className="px-4 py-3 text-gray-500 max-w-xs truncate">
                    {scan.source_url ?? "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
