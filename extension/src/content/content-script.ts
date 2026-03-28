/// <reference types="chrome" />

interface MediaInfo {
  type: "video" | "audio" | "image";
  payload: Record<string, unknown>;
}

/**
 * Scans the current page for detectable media elements.
 * Responds to GET_MEDIA_INFO messages from the popup.
 */
chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.action === "GET_MEDIA_INFO") {
    detectPageMedia().then(sendResponse);
    return true;
  }
});

async function detectPageMedia(): Promise<MediaInfo | null> {
  // 1. Check for video elements
  const video = document.querySelector<HTMLVideoElement>("video[src], video source");
  if (video) {
    const src =
      (video as HTMLVideoElement).src ||
      (video as unknown as HTMLSourceElement).src ||
      "";
    return { type: "video", payload: { url: src, frames: [] } };
  }

  // 2. Check for audio elements
  const audio = document.querySelector<HTMLAudioElement>("audio[src]");
  if (audio) {
    const audioB64 = await fetchAsBase64(audio.src);
    if (audioB64) {
      return {
        type: "audio",
        payload: { audio_base64: audioB64, duration_seconds: audio.duration || 0 },
      };
    }
  }

  // 3. Check for prominent images (largest visible image)
  const images = Array.from(document.querySelectorAll<HTMLImageElement>("img")).filter(
    (img) =>
      img.naturalWidth > 200 &&
      img.naturalHeight > 200 &&
      img.src.startsWith("http://") || img.src.startsWith("https://")
  );

  if (images.length > 0) {
    const largest = images.reduce((a, b) =>
      a.naturalWidth * a.naturalHeight > b.naturalWidth * b.naturalHeight ? a : b
    );
    const imgB64 = await fetchAsBase64(largest.src);
    if (imgB64) {
      return {
        type: "image",
        payload: { image_base64: imgB64, check_metadata: true },
      };
    }
  }

  return null;
}

async function fetchAsBase64(url: string): Promise<string | null> {
  try {
    const res = await fetch(url);
    const blob = await res.blob();
    return await new Promise<string>((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve((reader.result as string).split(",")[1]);
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  } catch {
    return null;
  }
}

// Inject visual warning overlay for flagged media
function injectWarningOverlay(element: HTMLElement, riskLevel: string) {
  const overlay = document.createElement("div");
  overlay.style.cssText = `
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(220, 38, 38, 0.15);
    border: 2px solid #dc2626;
    border-radius: 4px;
    z-index: 9999;
    pointer-events: none;
    display: flex;
    align-items: flex-start;
    padding: 4px;
  `;
  const badge = document.createElement("span");
  badge.style.cssText = `
    background: #dc2626;
    color: white;
    font-size: 11px;
    font-weight: bold;
    padding: 2px 6px;
    border-radius: 3px;
    font-family: sans-serif;
  `;
  badge.textContent = `⚠ TruthLens: ${riskLevel.toUpperCase()} RISK`;
  overlay.appendChild(badge);

  const parent = element.parentElement;
  if (parent) {
    parent.style.position = "relative";
    parent.appendChild(overlay);
  }
}

// Exported to satisfy isolatedModules; injectWarningOverlay available for future use
export { injectWarningOverlay };
