"use client";

import { montserrat } from "@/components/ui/fonts";
import { useComposeText } from "./use-compose-text";

export interface AnonymousCheckboxProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
}

/**
 * Checkbox "Gửi ẩn danh" (mms_G) — CHỈ bật/tắt, KHÔNG hiện thêm ô nhập tên
 * nào (clarifications gap #4: nhãn ẩn danh cố định, bỏ hẳn field tự nhập —
 * ghi đè lên mô tả "Bật: Hiển thị text field điền tên ẩn danh" trong spec
 * CSV gốc và TC_43/44, cả hai đều lỗi thời so với quyết định đã chốt).
 */
export function AnonymousCheckbox({ checked, onChange }: AnonymousCheckboxProps) {
  const t = useComposeText();

  return (
    <label className={`${montserrat.className} flex items-center gap-3 text-base font-bold text-[#00101A]`}>
      <input
        type="checkbox"
        checked={checked}
        onChange={(event) => onChange(event.target.checked)}
        className="h-5 w-5 accent-[#00101A]"
      />
      {t("anonymous.label")}
    </label>
  );
}
