"use client";

import type { ReactNode } from "react";

import { montserrat } from "@/components/ui/fonts";
import { useCommonUiT } from "@/components/ui/use-common-ui-text";

import type { NavItem } from "./site-header";

export interface SiteFooterProps {
  /** Chuỗi bản quyền đã dịch — thuộc namespace `common.json` (phase-01 sở hữu), trang cha truyền vào. */
  copyright: string;
  nav?: NavItem[];
  slot?: ReactNode;
}

/** Chrome footer dùng chung — xem ghi chú thiết kế ở `site-header.tsx`. */
export function SiteFooter({ copyright, nav, slot }: SiteFooterProps) {
  const t = useCommonUiT();
  return (
    <footer
      className={`${montserrat.className} mt-auto flex flex-wrap items-center justify-between gap-4 border-t border-[#998C5F] bg-[#00101A] px-6 py-6`}
    >
      <p className="text-sm text-white">{copyright}</p>
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
