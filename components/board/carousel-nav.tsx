"use client";

import type { ReactNode } from "react";

export interface NavOverlayProps {
  side: "left" | "right";
  onClick: () => void;
  disabled: boolean;
  label: string;
  children: ReactNode;
}

/**
 * Lớp phủ gradient + nút điều hướng (mm:13461 `Frame 528`/`Frame 527`, 400×525).
 * Lớp phủ `pointer-events-none` để không chặn click lên thẻ dưới; nút bên
 * trong bật lại `pointer-events-auto`. Ẩn dưới `sm` (suy đoán — Figma không có
 * breakpoint mobile); 120px ở `sm`/`md`, đúng 400px từ `lg`.
 */
export function NavOverlay({ side, onClick, disabled, label, children }: NavOverlayProps) {
  const isLeft = side === "left";
  return (
    <div
      className={`pointer-events-none absolute inset-y-0 z-10 hidden w-[120px] items-center sm:flex lg:w-[400px] ${
        isLeft ? "left-0 justify-start pl-4 lg:pl-20" : "right-0 justify-end pr-4 lg:pr-[140px]"
      }`}
      style={{
        background: isLeft
          ? "linear-gradient(90deg, #00101A 50%, rgba(255,255,255,0) 100%)"
          : "linear-gradient(270deg, #00101A 50%, rgba(255,255,255,0) 100%)",
      }}
    >
      <button
        type="button"
        onClick={onClick}
        disabled={disabled}
        aria-disabled={disabled}
        aria-label={label}
        className="pointer-events-auto flex h-20 w-20 shrink-0 items-center justify-center rounded p-2.5 text-white transition-opacity duration-200 ease-out enabled:hover:opacity-80 disabled:opacity-30 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FFEA9E] motion-reduce:transition-none"
      >
        {children}
      </button>
    </div>
  );
}
