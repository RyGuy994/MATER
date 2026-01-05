// filepath: MATER/MATER_FE/src/hooks/useToast.js
import { useState, useCallback } from "react";

/**
 * Hook to manage multiple toasts
 * Returns: { toasts, showToast, dismissToast }
 */
export function useToast() {
  const [toasts, setToasts] = useState([]);

  const showToast = useCallback((message, type = "success", duration = 4000) => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, message, type, duration }]);
    return id;
  }, []);

  const dismissToast = useCallback((id) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  }, []);

  return { toasts, showToast, dismissToast };
}
