"use client";

import Image from "next/image";
import { useEffect, useMemo, useRef, useState } from "react";

import { CloseIcon, PlusIcon } from "@/components/ui/icons";
import { montserrat } from "@/components/ui/fonts";
import { isAcceptedImageFile, MAX_IMAGES } from "./image-file-validation";
import { useComposeText } from "./use-compose-text";

export interface ImageUploadFieldProps {
  value: File[];
  onChange: (value: File[]) => void;
  errorMessage?: string;
}

/**
 * Trường "Image" (mms_F) — chọn tối đa 5 ảnh, nút "+ Image" tự ẩn khi đủ 5
 * (TC_19/38), ảnh vượt quá bị TỪ CHỐI thay vì cắt bớt (TC_20/54), và loại file
 * sai định dạng bị chặn kèm thông báo (TC_23/24/55).
 *
 * Lỗi ở đây là lỗi TƯƠNG TÁC tức thời (thử chọn ảnh thứ 6 / chọn sai định
 * dạng) — khác với `errorMessage` (lỗi do submit/server truyền vào từ
 * ngoài); cả hai cùng hiển thị chung một chỗ, ưu tiên lỗi tương tác vì nó mới
 * xảy ra gần nhất.
 */
export function ImageUploadField({ value, onChange, errorMessage }: ImageUploadFieldProps) {
  const t = useComposeText();
  const inputRef = useRef<HTMLInputElement>(null);
  const [interactionError, setInteractionError] = useState<string | null>(null);

  // Preview URL suy trực tiếp từ `value` (không cần state riêng — tránh
  // setState đồng bộ trong effect, `react-hooks/set-state-in-effect` coi đây
  // là giá trị TÍNH ĐƯỢC từ props, không phải side-effect thật). Effect bên
  // dưới CHỈ lo dọn dẹp (thu hồi object URL cũ), không gọi setState nào.
  const previewUrls = useMemo(() => value.map((file) => URL.createObjectURL(file)), [value]);
  useEffect(() => {
    return () => previewUrls.forEach((url) => URL.revokeObjectURL(url));
  }, [previewUrls]);

  function handleFilesSelected(fileList: FileList | null) {
    if (!fileList || fileList.length === 0) return;
    const files = Array.from(fileList);

    const invalidType = files.some((file) => !isAcceptedImageFile(file));
    const accepted = files.filter(isAcceptedImageFile);
    const remainingSlots = Math.max(0, MAX_IMAGES - value.length);
    const exceedsMax = accepted.length > remainingSlots;

    if (invalidType) {
      setInteractionError(t("image.invalidType"));
    } else if (exceedsMax) {
      setInteractionError(t("image.maxReached"));
    } else {
      setInteractionError(null);
    }

    if (remainingSlots > 0 && accepted.length > 0) {
      onChange([...value, ...accepted.slice(0, remainingSlots)]);
    }

    if (inputRef.current) inputRef.current.value = ""; // cho phép chọn lại đúng file vừa chọn lần sau
  }

  function remove(index: number) {
    onChange(value.filter((_, i) => i !== index));
    setInteractionError(null);
  }

  const canAddMore = value.length < MAX_IMAGES;
  const displayedError = interactionError ?? errorMessage;

  return (
    <div className={`${montserrat.className} flex flex-col gap-2`}>
      <span className="text-[22px] font-bold text-[#00101A]">{t("image.label")}</span>
      <div className="flex flex-wrap items-center gap-3">
        {value.map((file, index) => (
          // Key ghép tên file + vị trí: cùng một ảnh có thể được thêm 2 lần
          // (trùng tên + kích thước), `key={file.name}` đơn thuần sẽ đụng độ
          // — đúng bẫy đã gặp ở `kudo-card.tsx` phase-09 với `image.url`.
          <div key={`${file.name}-${index}`} className="relative h-[88px] w-[88px]">
            {previewUrls[index] && (
              <Image
                src={previewUrls[index]}
                alt=""
                width={88}
                height={88}
                unoptimized
                className="h-[88px] w-[88px] rounded-[18px] border border-[#998C5F] object-cover"
              />
            )}
            <button
              type="button"
              onClick={() => remove(index)}
              aria-label={t("image.removeAria").replace("{index}", String(index + 1))}
              className="absolute -top-2 -right-2 flex h-6 w-6 items-center justify-center rounded-full bg-[#00101A] text-white"
            >
              <CloseIcon className="h-3.5 w-3.5" />
            </button>
          </div>
        ))}
        {canAddMore && (
          <button
            type="button"
            onClick={() => inputRef.current?.click()}
            className="flex h-[88px] w-[88px] flex-col items-center justify-center gap-1 rounded-[18px] border border-dashed border-[#998C5F] text-[#00101A]"
          >
            <PlusIcon className="h-6 w-6" />
            <span className="text-xs font-bold">{t("image.addButton")}</span>
          </button>
        )}
        <span className="text-sm font-bold text-[#999999]">{t("image.maxHint")}</span>
      </div>
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        multiple
        className="hidden"
        onChange={(event) => handleFilesSelected(event.target.files)}
      />
      {displayedError && <span className="text-sm font-bold text-[#B3261E]">{displayedError}</span>}
    </div>
  );
}
