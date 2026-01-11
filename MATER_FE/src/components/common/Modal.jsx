/* filepath: MATER_FE/src/components/common/Modal.jsx */

import React, { useEffect } from "react";
import { createPortal } from "react-dom";
import "../assets/AssetsManager.css"; // ensures modal-overlay/modal-content styles exist

export default function Modal({ open, onClose, title, children }) {
  useEffect(() => {
    if (!open) return;

    const onKeyDown = (e) => {
      if (e.key === "Escape") onClose?.();
    };

    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [open, onClose]);

  if (!open) return null;

  return createPortal(
    <div
      className="modal-overlay"
      onMouseDown={(e) => {
        // click outside closes
        if (e.target === e.currentTarget) onClose?.();
      }}
      role="dialog"
      aria-modal="true"
      aria-label={title || "Modal"}
    >
      <div className="modal-content" onMouseDown={(e) => e.stopPropagation()}>
        {title ? <h3 style={{ marginTop: 0 }}>{title}</h3> : null}
        {children}
      </div>
    </div>,
    document.body
  );
}
