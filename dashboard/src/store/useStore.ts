import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { ScanRecord } from "../api/client";

interface AuthState {
  token: string | null;
  userId: string | null;
  apiKey: string | null;
}

interface AppState {
  auth: AuthState;
  scans: ScanRecord[];
  isLoading: boolean;

  setAuth: (auth: Partial<AuthState>) => void;
  logout: () => void;
  setScans: (scans: ScanRecord[]) => void;
  addScan: (scan: ScanRecord) => void;
  setLoading: (v: boolean) => void;
}

export const useStore = create<AppState>()(
  persist(
    (set) => ({
      auth: { token: null, userId: null, apiKey: null },
      scans: [],
      isLoading: false,

      setAuth: (auth) =>
        set((state) => ({ auth: { ...state.auth, ...auth } })),

      logout: () => {
        localStorage.removeItem("tl_token");
        set({ auth: { token: null, userId: null, apiKey: null }, scans: [] });
      },

      setScans: (scans) => set({ scans }),
      addScan: (scan) => set((state) => ({ scans: [scan, ...state.scans] })),
      setLoading: (isLoading) => set({ isLoading }),
    }),
    {
      name: "truthlens-store",
      partialize: (state) => ({ auth: state.auth }),
    }
  )
);
