import React, { useEffect, useState } from "react";
import "../index.css";
import RiskBadge from "../components/RiskBadge";
import ScanResult from "../components/ScanResult";
import ReactDOM from "react-dom/client";

interface ScanState {
  status: "idle" | "scanning" | "done" | "error";
  result?: {
    type: "video" | "audio" | "image";
    is_fake: boolean;
    confidence: number;
    risk_level: string;
    details: Record<string, unknown>;
  };
  url?: string;
  error?: string;
}

const API_BASE = "http://localhost:8000";

export default function Popup() {
  const [scan, setScan] = useState<ScanState>({ status: "idle" });
  const [apiKey, setApiKey] = useState<string>("");
  const [currentTab, setCurrentTab] = useState<chrome.tabs.Tab | null>(null);

  useEffect(() => {
    chrome.storage.local.get(["apiKey"], (res) => {
      if (res.apiKey) setApiKey(res.apiKey);
    });
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      setCurrentTab(tabs[0] ?? null);
    });
  }, []);

  const saveApiKey = () => {
    chrome.storage.local.set({ apiKey });
  };

  const scanCurrentPage = async () => {
    if (!apiKey) {
      setScan({ status: "error", error: "Please enter your API key first." });
      return;
    }
    setScan({ status: "scanning", url: currentTab?.url });

    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      const response = await chrome.tabs.sendMessage(tab.id!, { action: "GET_MEDIA_INFO" });

      if (!response) {
        setScan({ status: "error", error: "No media found on this page." });
        return;
      }

      const { type, payload } = response;
      const endpoint = `${API_BASE}/api/detect/${type}`;

      const res = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${apiKey}`,
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        throw new Error(`API error ${res.status}`);
      }

      const data = await res.json();

      setScan({
        status: "done",
        url: currentTab?.url,
        result: {
          type,
          is_fake: data.is_deepfake ?? data.is_cloned ?? data.is_ai_generated,
          confidence: data.confidence,
          risk_level: data.risk_level ?? (data.is_cloned ? "high" : "low"),
          details: data,
        },
      });
    } catch (err: unknown) {
      setScan({
        status: "error",
        error: err instanceof Error ? err.message : "Unknown error",
      });
    }
  };

  return (
    <div className="p-4 min-h-36 font-sans">
      {/* Header */}
      <div className="flex items-center gap-2 mb-4">
        <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-xs font-bold">
          TL
        </div>
        <h1 className="text-lg font-bold tracking-tight">TruthLens</h1>
        {scan.result && <RiskBadge level={scan.result.risk_level} />}
      </div>

      {/* API Key input */}
      {!apiKey && (
        <div className="mb-4">
          <label className="text-xs text-gray-400 block mb-1">API Key</label>
          <div className="flex gap-2">
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="tl_..."
              className="flex-1 text-xs bg-gray-800 border border-gray-700 rounded px-2 py-1 outline-none"
            />
            <button
              onClick={saveApiKey}
              className="text-xs bg-blue-600 hover:bg-blue-700 px-2 py-1 rounded"
            >
              Save
            </button>
          </div>
        </div>
      )}

      {/* Scan button */}
      <button
        onClick={scanCurrentPage}
        disabled={scan.status === "scanning"}
        className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-sm font-medium py-2 rounded-lg mb-4 transition-colors"
      >
        {scan.status === "scanning" ? "Scanning…" : "Scan This Page"}
      </button>

      {/* Results */}
      {scan.status === "done" && scan.result && (
        <ScanResult result={scan.result} />
      )}

      {scan.status === "error" && (
        <p className="text-red-400 text-xs">{scan.error}</p>
      )}

      {scan.url && (
        <p className="text-gray-500 text-xs mt-3 truncate" title={scan.url}>
          {scan.url}
        </p>
      )}
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <Popup />
  </React.StrictMode>
);
