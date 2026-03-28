import { useState, useEffect } from "react";
import { useStore } from "../store/useStore";
import { authApi } from "../api/client";

export default function Settings() {
  const { auth, setAuth, logout } = useStore();
  const [apiKey, setApiKey] = useState(auth.apiKey ?? "");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [mode, setMode] = useState<"login" | "register">("login");
  const [msg, setMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);

  useEffect(() => {
    setApiKey(auth.apiKey ?? "");
  }, [auth.apiKey]);

  const handleAuth = async () => {
    setMsg(null);
    try {
      const res =
        mode === "login"
          ? await authApi.login(email, password)
          : await authApi.register(email, password, name);
      const { access_token, user_id } = res.data as { access_token: string; user_id: string };
      localStorage.setItem("tl_token", access_token);
      setAuth({ token: access_token, userId: user_id });
      setMsg({ type: "success", text: "Authenticated successfully!" });
    } catch {
      setMsg({ type: "error", text: "Authentication failed. Check credentials." });
    }
  };

  const handleGetApiKey = async () => {
    setMsg(null);
    try {
      const res = await authApi.getApiKey();
      const key = (res.data as { api_key: string }).api_key;
      setAuth({ apiKey: key });
      setApiKey(key);
      setMsg({ type: "success", text: "API key generated." });
    } catch {
      setMsg({ type: "error", text: "Failed to generate API key." });
    }
  };

  return (
    <div className="space-y-8 max-w-lg">
      <h1 className="text-3xl font-bold">Settings</h1>

      {/* Auth section */}
      {!auth.token ? (
        <div className="bg-gray-900 rounded-xl p-6 space-y-4">
          <h2 className="text-lg font-semibold">Account</h2>
          <div className="flex gap-2">
            {(["login", "register"] as const).map((m) => (
              <button
                key={m}
                onClick={() => setMode(m)}
                className={`text-sm px-4 py-1.5 rounded-lg capitalize transition-colors ${mode === m ? "bg-blue-600 text-white" : "bg-gray-800 text-gray-400 hover:text-white"}`}
              >
                {m}
              </button>
            ))}
          </div>
          {mode === "register" && (
            <input
              type="text"
              placeholder="Name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-sm outline-none focus:border-blue-500"
            />
          )}
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-sm outline-none focus:border-blue-500"
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-sm outline-none focus:border-blue-500"
          />
          <button
            onClick={handleAuth}
            className="w-full bg-blue-600 hover:bg-blue-700 py-2 rounded-lg text-sm font-medium transition-colors"
          >
            {mode === "login" ? "Login" : "Register"}
          </button>
        </div>
      ) : (
        <div className="bg-gray-900 rounded-xl p-6 space-y-4">
          <h2 className="text-lg font-semibold">Account</h2>
          <p className="text-sm text-gray-400">User ID: <span className="text-white font-mono text-xs">{auth.userId}</span></p>
          <button onClick={logout} className="text-sm text-red-400 hover:text-red-300 transition-colors">
            Logout
          </button>
        </div>
      )}

      {/* API Key */}
      {auth.token && (
        <div className="bg-gray-900 rounded-xl p-6 space-y-4">
          <h2 className="text-lg font-semibold">API Key</h2>
          {apiKey ? (
            <div className="bg-gray-800 rounded-lg px-4 py-3">
              <p className="text-xs font-mono text-green-400 break-all">{apiKey}</p>
            </div>
          ) : (
            <p className="text-sm text-gray-400">No API key yet.</p>
          )}
          <button
            onClick={handleGetApiKey}
            className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          >
            {apiKey ? "Regenerate API Key" : "Generate API Key"}
          </button>
          <p className="text-xs text-gray-500">Use this key in the Chrome extension to authenticate scans.</p>
        </div>
      )}

      {msg && (
        <div className={`text-sm px-4 py-3 rounded-lg ${msg.type === "success" ? "bg-green-900/50 text-green-300" : "bg-red-900/50 text-red-300"}`}>
          {msg.text}
        </div>
      )}
    </div>
  );
}
