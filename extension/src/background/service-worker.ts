/// <reference types="chrome" />

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

// Install alarm for periodic checks
chrome.runtime.onInstalled.addListener(() => {
  chrome.alarms.create("periodicCheck", { periodInMinutes: 5 });
  console.log("[TruthLens] Extension installed.");
});

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === "periodicCheck") {
    console.log("[TruthLens] Periodic check tick.");
  }
});

// Message relay between content script and popup
chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.action === "SCAN_MEDIA") {
    handleScanMedia(message.payload as Record<string, unknown>, message.mediaType as string)
      .then(sendResponse)
      .catch((err: Error) => sendResponse({ error: err.message }));
    return true; // keep channel open for async
  }
});

async function handleScanMedia(
  payload: Record<string, unknown>,
  mediaType: string
): Promise<unknown> {
  const apiKey = await getApiKey();
  if (!apiKey) throw new Error("No API key configured");

  const res = await fetch(`${API_BASE}/api/detect/${mediaType}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify(payload),
  });

  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json();
}

async function getApiKey(): Promise<string | null> {
  return new Promise((resolve) => {
    chrome.storage.local.get(["apiKey"], (res) => resolve((res.apiKey as string) ?? null));
  });
}
