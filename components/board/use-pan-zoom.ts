"use client";

/**
 * Hook pan/zoom cho canvas word-cloud Spotlight (`spotlight-section.tsx`) —
 * quản lý state translate/scale, xử lý kéo bằng con trỏ, cuộn chuột để zoom,
 * và điều hướng bàn phím (mũi tên pan, +/− zoom). Scale luôn kẹp trong
 * [MIN_SCALE, MAX_SCALE].
 */

import { useEffect, useRef, useState } from "react";
import type { KeyboardEvent as ReactKeyboardEvent, PointerEvent as ReactPointerEvent } from "react";

import { clamp } from "./spotlight-layout";

const MIN_SCALE = 0.5;
const MAX_SCALE = 2.5;
const ZOOM_STEP = 0.15;
const PAN_STEP = 24;
/** Ngưỡng di chuyển (px) để phân biệt kéo-pan với click chọn tên. */
const DRAG_THRESHOLD = 4;

export interface PanZoomTransform {
  x: number;
  y: number;
  scale: number;
}

export function usePanZoom() {
  const [transform, setTransform] = useState<PanZoomTransform>({ x: 0, y: 0, scale: 1 });
  const [isDragging, setIsDragging] = useState(false);

  const canvasRef = useRef<HTMLDivElement>(null);
  const dragRef = useRef<{ startX: number; startY: number; originX: number; originY: number } | null>(null);
  const wasDraggedRef = useRef(false);

  // Wheel cần listener native `{ passive: false }` để `preventDefault` hoạt
  // động — React gắn `onWheel` synthetic ở chế độ passive, gọi preventDefault
  // trong đó chỉ tạo cảnh báo console chứ không chặn được cuộn trang.
  useEffect(() => {
    const el = canvasRef.current;
    if (!el) return;
    const handleWheelNative = (e: WheelEvent) => {
      e.preventDefault();
      const delta = e.deltaY > 0 ? -ZOOM_STEP : ZOOM_STEP;
      setTransform((prev) => ({ ...prev, scale: clamp(prev.scale + delta, MIN_SCALE, MAX_SCALE) }));
    };
    el.addEventListener("wheel", handleWheelNative, { passive: false });
    return () => el.removeEventListener("wheel", handleWheelNative);
  }, []);

  function adjustZoom(delta: number) {
    setTransform((prev) => ({ ...prev, scale: clamp(prev.scale + delta, MIN_SCALE, MAX_SCALE) }));
  }

  /**
   * MỘT nút cho cả phóng to lẫn trả về mặc định — bản vẽ chỉ vẽ đúng một control
   * (`B.7.2_Pan zoom`, 30×30 góc dưới-phải), không phải cặp `+`/`−`.
   *
   * Mỗi lần bấm phóng thêm một nấc; chạm trần thì đưa cả scale lẫn vị trí về mặc
   * định, nên không bao giờ có ngõ cụt "phóng to rồi không lùi được bằng chuột".
   * Zoom ra từng nấc vẫn còn nguyên ở cuộn chuột và phím `-`.
   */
  function cycleZoom() {
    setTransform((prev) =>
      prev.scale >= MAX_SCALE - 1e-6
        ? { x: 0, y: 0, scale: 1 }
        : { ...prev, scale: clamp(prev.scale + ZOOM_STEP, MIN_SCALE, MAX_SCALE) },
    );
  }

  function handlePointerDown(e: ReactPointerEvent<HTMLDivElement>) {
    e.currentTarget.setPointerCapture(e.pointerId);
    wasDraggedRef.current = false;
    dragRef.current = { startX: e.clientX, startY: e.clientY, originX: transform.x, originY: transform.y };
    setIsDragging(true);
  }

  function handlePointerMove(e: ReactPointerEvent<HTMLDivElement>) {
    const drag = dragRef.current;
    if (!drag) return;
    const dx = e.clientX - drag.startX;
    const dy = e.clientY - drag.startY;
    if (Math.abs(dx) > DRAG_THRESHOLD || Math.abs(dy) > DRAG_THRESHOLD) {
      wasDraggedRef.current = true;
    }
    setTransform((prev) => ({ ...prev, x: drag.originX + dx, y: drag.originY + dy }));
  }

  function handlePointerUp() {
    dragRef.current = null;
    setIsDragging(false);
  }

  function handleKeyDown(e: ReactKeyboardEvent<HTMLDivElement>) {
    switch (e.key) {
      case "ArrowUp":
        e.preventDefault();
        setTransform((prev) => ({ ...prev, y: prev.y + PAN_STEP }));
        break;
      case "ArrowDown":
        e.preventDefault();
        setTransform((prev) => ({ ...prev, y: prev.y - PAN_STEP }));
        break;
      case "ArrowLeft":
        e.preventDefault();
        setTransform((prev) => ({ ...prev, x: prev.x + PAN_STEP }));
        break;
      case "ArrowRight":
        e.preventDefault();
        setTransform((prev) => ({ ...prev, x: prev.x - PAN_STEP }));
        break;
      case "+":
      case "=":
        e.preventDefault();
        adjustZoom(ZOOM_STEP);
        break;
      case "-":
      case "_":
        e.preventDefault();
        adjustZoom(-ZOOM_STEP);
        break;
      default:
        break;
    }
  }

  /** True nếu lần kéo gần nhất vượt ngưỡng — dùng để bỏ qua click "dính theo" sau khi pan. */
  function wasDragged(): boolean {
    return wasDraggedRef.current;
  }

  // `motion-reduce:transition-none` (quy ước đã dùng ở board-banner.tsx/kudo-card.tsx)
  // tự tắt transition theo `prefers-reduced-motion` — không cần tự viết matchMedia.
  // Khi đang kéo (`isDragging`) thì luôn bỏ transition để pan bám theo con trỏ tức thời.
  const transitionClass = isDragging ? "" : "transition-transform duration-150 ease-out motion-reduce:transition-none";

  return {
    canvasRef,
    transform,
    transitionClass,
    handlePointerDown,
    handlePointerMove,
    handlePointerUp,
    handleKeyDown,
    wasDragged,
    cycleZoom,
  };
}
