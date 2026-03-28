import React from "react";

interface Props {
  result: {
    type: string;
    is_fake: boolean;
    confidence: number;
    risk_level: string;
    details: Record<string, unknown>;
  };
}

export default function ScanResult({ result }: Props) {
  const pct = Math.round(result.confidence * 100);
  const barColor = result.is_fake ? "bg-red-500" : "bg-green-500";

  return (
    <div className="space-y-3">
      <div
        className={`text-center text-sm font-bold py-2 rounded-lg ${
          result.is_fake ? "bg-red-900/60 text-red-300" : "bg-green-900/60 text-green-300"
        }`}
      >
        {result.is_fake ? "⚠️ Potential Deepfake Detected" : "✅ Appears Authentic"}
      </div>

      {/* Confidence bar */}
      <div>
        <div className="flex justify-between text-xs text-gray-400 mb-1">
          <span>Confidence</span>
          <span>{pct}%</span>
        </div>
        <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
          <div className={`h-full ${barColor} transition-all`} style={{ width: `${pct}%` }} />
        </div>
      </div>

      {/* Media type */}
      <div className="text-xs text-gray-400">
        Scan type: <span className="text-white capitalize">{result.type}</span>
      </div>

      {result.type === "video" &&
        Array.isArray((result.details as Record<string, unknown[]>).frame_scores) && (
          <div className="text-xs text-gray-400">
            Frames analysed:{" "}
            {(result.details as Record<string, unknown[]>).frame_scores.length}
          </div>
        )}
      {result.type === "audio" &&
        (result.details as Record<string, unknown>).synthesis_model_guess && (
          <div className="text-xs text-gray-400">
            Suspected model:{" "}
            <span className="text-yellow-300">
              {String((result.details as Record<string, unknown>).synthesis_model_guess)}
            </span>
          </div>
        )}
      {result.type === "image" &&
        (result.details as Record<string, unknown>).generator_model_guess && (
          <div className="text-xs text-gray-400">
            Suspected generator:{" "}
            <span className="text-yellow-300">
              {String((result.details as Record<string, unknown>).generator_model_guess)}
            </span>
          </div>
        )}
    </div>
  );
}
