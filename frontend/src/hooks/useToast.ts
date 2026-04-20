import { useState, useCallback } from "react";

export function useToast() {
  const [toast, setToast] = useState<string | null>(null);

  const handleCopy = useCallback((value: string) => {
    setToast(`Copied: ${value.length > 40 ? value.slice(0, 40) + "…" : value}`);
  }, []);

  const showToast = useCallback((message: string) => {
    setToast(message);
  }, []);

  const dismissToast = useCallback(() => {
    setToast(null);
  }, []);

  return {
    toast,
    setToast: showToast,
    dismissToast,
    handleCopy,
  };
}
