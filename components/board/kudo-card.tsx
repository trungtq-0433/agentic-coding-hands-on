"use client";

/**
 * Thẻ KUDO — Figma `mms_C.3_KUDO Post` (node 3127:21871, 680×749). Phase-11
 * (Profile) dùng lại NGUYÊN VẸN (TC_WEB_PROFILE_GUI_006) — mọi hành vi qua
 * props, không tự fetch (xem `kudo-card-types.ts`).
 *
 * Số tim KHÔNG tự tăng lạc quan (TC_WEB_PROFILE_FUN_014): luôn hiện đúng
 * `kudo.heartCount` truyền vào; trang cha đổi số sau khi server xác nhận.
 * `pending` disable nút tim để chặn double-click sinh nhiều lời gọi song song
 * (bấm 5 lần nhanh chỉ 1 lời gọi rời đi).
 *
 * Icon tim/link/send/pen dùng chung từ `board-icons.tsx` (icon tim đổi màu
 * xám/đỏ theo `hearted`, cùng lý do với `components/ui/icons.tsx`). Icon bút
 * ở đây khớp path thật trong `icon-pen.svg` — trước đó bị chép sai thành một
 * path tự đơn giản hoá, nay đã sửa cho khớp bản thiết kế.
 *
 * **`variant` (mm:3127:21871 `feed` 680px / mm:2940:13464 `highlight` 528px):**
 * thẻ trong carousel Highlight và thẻ trong feed là CÙNG một component —
 * chỉ khác kích thước, padding, bo góc và viền. Mọi hành vi/logic bên trong
 * (tim không tự tăng lạc quan, `pending` disable nút tim…) giữ NGUYÊN cho
 * cả hai biến thể.
 */

import Image from "next/image";
import { useMemo } from "react";

import { montserrat } from "@/components/ui/fonts";
import { UserIcon } from "@/components/ui/icons";
import { useLocale } from "@/lib/i18n/locale-provider";
import { HeartIcon, LinkIcon, PenIcon, SendIcon } from "./board-icons";
import { HeroBadge } from "./hero-badge";
import { useBoardT } from "./use-board-text";
import type { KudoCardData, KudoParticipant } from "./kudo-card-types";

export interface KudoCardProps {
  kudo: KudoCardData;
  /** Đang gọi server cho thẻ này → disable icon tim. */
  pending?: boolean;
  /** `"feed"` (mặc định, 680px) hay `"highlight"` (carousel, 528px + viền vàng 4px). */
  variant?: "feed" | "highlight";
  onToggleHeart: (kudosId: number) => void;
  onCopyLink: (kudosId: number) => void;
  onOpenProfile: (userId: string) => void;
}

/** Khung ngoài đổi theo biến thể — mọi nội dung bên trong dùng chung nguyên vẹn. */
const CARD_VARIANT_CLASS: Record<NonNullable<KudoCardProps["variant"]>, string> = {
  feed: "w-full max-w-[680px] rounded-3xl px-4 pt-6 pb-4 sm:px-10 sm:pt-10",
  highlight: "w-[528px] max-w-[528px] shrink-0 rounded-2xl border-4 border-[#FFEA9E] px-6 pt-6 pb-4",
};

interface ParticipantBlockProps { participant: KudoParticipant; t: (key: string) => string; onOpenProfile: (userId: string) => void }

function ParticipantBlock({ participant, t, onOpenProfile }: ParticipantBlockProps) {
  const participantId = participant.id;
  const body = (
    <>
      {participant.avatarUrl ? (
        <Image src={participant.avatarUrl} alt="" width={64} height={64} className="h-16 w-16 rounded-full border-[1.869px] border-white object-cover" />
      ) : (
        <span className="flex h-16 w-16 items-center justify-center rounded-full border-[1.869px] border-white bg-[#00101A]">
          <UserIcon className="h-8 w-8 text-[#FFEA9E]" />
        </span>
      )}
      <span className="text-base font-bold text-[#00101A]">
        {participantId === null ? t("card.anonymous") : (participant.name ?? t("card.anonymous"))}
      </span>
      {(participant.heroTier || participant.starCount > 0) && (
        <span className="flex items-center gap-0.5">
          <HeroBadge tier={participant.heroTier} />
          {participant.starCount > 0 && (
            <span aria-label={t("card.starsAria")} className="text-sm font-bold text-[#D4271D]">
              {"★".repeat(participant.starCount)}
            </span>
          )}
        </span>
      )}
    </>
  );
  if (participantId === null) {
    return <div className="flex flex-1 flex-col items-center gap-[13px] text-center">{body}</div>;
  }

  return (
    <button
      type="button"
      onClick={() => onOpenProfile(participantId)}
      className="flex flex-1 flex-col items-center gap-[13px] text-center transition-opacity duration-200 ease-out hover:opacity-80 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#D4271D] motion-reduce:transition-none"
    >
      {body}
    </button>
  );
}

export function KudoCard({ kudo, pending = false, variant = "feed", onToggleHeart, onCopyLink, onOpenProfile }: KudoCardProps) {
  const t = useBoardT();
  const locale = useLocale();

  // `createdAtIso` đến từ ngoài hệ thống — ngày không hợp lệ thì hiện chuỗi gốc thay vì crash Intl.
  const formattedTime = useMemo(() => {
    const date = new Date(kudo.createdAtIso);
    if (Number.isNaN(date.getTime())) return kudo.createdAtIso;
    const intlLocale = locale === "vi" ? "vi-VN" : "en-US";
    const timeStr = new Intl.DateTimeFormat(intlLocale, {
      hour: "2-digit",
      minute: "2-digit",
      hourCycle: "h23",
      timeZone: "Asia/Ho_Chi_Minh",
    }).format(date);
    const dateStr = new Intl.DateTimeFormat(intlLocale, {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      timeZone: "Asia/Ho_Chi_Minh",
    }).format(date);
    return `${timeStr} - ${dateStr}`;
  }, [kudo.createdAtIso, locale]);

  return (
    <div className={`${montserrat.className} flex flex-col gap-4 bg-[#FFF8E1] ${CARD_VARIANT_CLASS[variant]}`}>
      {/* Info user */}
      <div className="flex flex-col items-center gap-6 sm:flex-row sm:justify-between">
        <ParticipantBlock participant={kudo.sender} t={t} onOpenProfile={onOpenProfile} />
        <span className="py-4" aria-hidden="true">
          <SendIcon className="h-8 w-8 text-[#00101A]" />
        </span>
        <ParticipantBlock participant={kudo.recipient} t={t} onOpenProfile={onOpenProfile} />
      </div>
      <div className="h-px w-full bg-[#FFEA9E]" />
      {/* Content */}
      <div className="flex flex-col gap-4">
        <p className="text-base leading-6 font-bold tracking-[0.5px] text-[#999999]">{formattedTime}</p>
        {kudo.title !== null && (
          <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-2">
            <span />
            <span className="text-center text-base leading-6 font-bold tracking-[0.5px] text-[#00101A]">{kudo.title}</span>
            <PenIcon className="h-8 w-8 justify-self-end text-[#00101A]" aria-hidden="true" />
          </div>
        )}
        <div className="rounded-xl border border-[#FFEA9E] bg-[#FFEA9E]/40 px-6 py-4">
          <p className="line-clamp-5 text-base leading-6 whitespace-pre-wrap text-[#00101A]">{kudo.body}</p>
        </div>
        {kudo.images.length > 0 && (
          <div className="flex gap-4 overflow-x-auto" aria-label={t("card.imagesAria")}>
            {/* Key ghép id thẻ + vị trí, KHÔNG dùng `image.url`: một kudo hoàn toàn
                có thể đính cùng một ảnh hai lần, và React sẽ báo trùng key rồi
                bỏ bớt phần tử. */}
            {kudo.images.slice(0, 5).map((image, index) => (
              <Image
                key={`${kudo.id}-${index}`}
                src={image.url}
                alt=""
                width={image.width ?? 88}
                height={image.height ?? 88}
                className="h-[88px] w-[88px] shrink-0 rounded-[18px] border border-[#998C5F] bg-white object-cover"
                priority={index === 0}
              />
            ))}
          </div>
        )}
        {kudo.hashtags.length > 0 && (
          <p className="text-base leading-6 font-bold tracking-[0.5px] text-[#D4271D]">
            {kudo.hashtags.map((tag) => `#${tag}`).join(" ")}
          </p>
        )}
      </div>
      <div className="h-px w-full bg-[#FFEA9E]" />
      {/* C.4_Button */}
      <div className="flex w-full items-center justify-between">
        <button
          type="button"
          onClick={() => onToggleHeart(kudo.id)}
          disabled={pending}
          aria-disabled={pending}
          aria-label={kudo.hearted ? t("card.unheartAria") : t("card.heartAria")}
          className="flex items-center gap-2 rounded transition-colors duration-200 ease-out focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#D4271D] motion-reduce:transition-none disabled:cursor-not-allowed disabled:opacity-50"
        >
          <span className="text-2xl leading-8 font-bold text-[#00101A]">{kudo.heartCount}</span>
          <HeartIcon className={`h-8 w-8 ${kudo.hearted ? "text-[#D4271D]" : "text-[#999999]"}`} />
        </button>
        <button
          type="button"
          onClick={() => onCopyLink(kudo.id)}
          className="flex h-14 w-36 items-center justify-center gap-2 rounded p-4 text-base leading-6 font-bold text-[#00101A] transition-colors duration-200 ease-out hover:bg-[#FFEA9E] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#D4271D] motion-reduce:transition-none"
        >
          {t("card.copyLink")}
          <LinkIcon className="h-6 w-6" />
        </button>
      </div>
    </div>
  );
}
