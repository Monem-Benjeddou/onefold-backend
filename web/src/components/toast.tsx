"use client";

import { createContext, useCallback, useContext, useState, type ReactNode } from "react";

import { CheckIcon, CrossIcon, InfoIcon } from "./icons";

type Tone = "success" | "error" | "info";
type Toast = { id: number; tone: Tone; message: string };

const ToastContext = createContext<(message: string, tone?: Tone) => void>(() => undefined);

/** Brief, non-blocking confirmations ("Saved", "Copied"), announced politely. */
export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const show = useCallback((message: string, tone: Tone = "success") => {
    const id = Date.now() + Math.random();
    setToasts((all) => [...all.slice(-2), { id, tone, message }]);
    setTimeout(() => setToasts((all) => all.filter((t) => t.id !== id)), tone === "error" ? 7000 : 3500);
  }, []);

  return (
    <ToastContext.Provider value={show}>
      {children}
      <div
        aria-live="polite"
        className="pointer-events-none fixed inset-x-4 bottom-24 z-50 flex flex-col items-center gap-2 lg:inset-x-auto lg:bottom-8 lg:right-8 lg:items-end"
      >
        {toasts.map((toast) => (
          <div
            key={toast.id}
            role={toast.tone === "error" ? "alert" : "status"}
            className="pointer-events-auto flex max-w-sm items-center gap-2.5 border-2 border-ink bg-ink px-4 py-3 text-sm font-medium text-paper shadow-hard-orange motion-safe:animate-[fold-in_200ms_ease-out]"
          >
            {toast.tone === "success" ? (
              <CheckIcon size={16} className="text-patina-light" />
            ) : toast.tone === "error" ? (
              <CrossIcon size={16} className="text-orange" />
            ) : (
              <InfoIcon size={16} />
            )}
            {toast.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  return useContext(ToastContext);
}
