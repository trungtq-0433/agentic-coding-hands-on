"use client";

import type { ReactNode } from "react";

import { montserratAlternates } from "@/components/ui/fonts";
import { useCommonUiT } from "@/components/ui/use-common-ui-text";

import type { NavItem } from "./site-header";

export interface SiteFooterProps {
  /** Chuỗi bản quyền đã dịch — thuộc namespace `common.json` (phase-01 sở hữu), trang cha truyền vào. */
  copyright: string;
  nav?: NavItem[];
  slot?: ReactNode;
}

/**
 * Chrome footer dùng chung — dựng theo ĐÚNG component Figma `mms_D_Footer`
 * (`342:1427`, đo trên màn Login `GzbNeVGJHz`):
 *
 *   padding 40px 90px · border-top 1px #2E3940
 *   chữ bản quyền: Montserrat Alternates 700, 16px/24px, CĂN GIỮA
 *
 * Bản đầu dùng `justify-between` với đúng MỘT con nên chữ dạt sang trái — Figma
 * đặt nó ở x 582→857, tâm 719.5 trên khung 1440, tức chính giữa. Khi có thêm
 * `nav`/`slot` thì mới cần space-between; không có thì căn giữa.
 * Màu viền cũng sai: `#998C5F` (token suy đoán của phase-06) → đúng là `#2E3940`.
 */
export function SiteFooter({ copyright, nav, slot }: SiteFooterProps) {
  const t = useCommonUiT();
  const hasSides = (nav !== undefined && nav.length > 0) || slot !== undefined;
  return (
    <footer
      className={`${montserratAlternates.className} mt-auto flex flex-wrap items-center gap-4 border-t border-[#2E3940] bg-[#00101A] px-6 py-10 md:px-[90px] ${
        hasSides ? "justify-between" : "justify-center"
      }`}
    >
      <p className="text-center text-base leading-6 font-bold text-white">{copyright}</p>
      {nav && nav.length > 0 && (
        <nav aria-label={t("siteFooter.navAria")} className="flex flex-wrap gap-4">
          {nav.map((item) => (
            <a key={item.href} href={item.href} className="text-sm font-bold text-white hover:text-[#FFEA9E]">
              {item.label}
            </a>
          ))}
        </nav>
      )}
      {slot && <div className="flex items-center gap-3">{slot}</div>}
    </footer>
  );
}
