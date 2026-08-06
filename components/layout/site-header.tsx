"use client";

import type { ReactNode } from "react";

import { montserrat } from "@/components/ui/fonts";
import { useCommonUiT } from "@/components/ui/use-common-ui-text";

export interface NavItem {
  label: string;
  href: string;
  active?: boolean;
}

export interface SiteHeaderProps {
  appName: string;
  nav: NavItem[];
  /** Vùng bên phải header do trang cha bơm vào (AccountMenu, LanguageSwitcher, nút đăng nhập...). */
  slot?: ReactNode;
}

/**
 * Chrome header dùng chung cho mọi trang. Không có screenId Figma riêng cho
 * header/footer trong 9 màn được giao — dựng theo design token dùng chung
 * (nền #00101A, viền #998C5F, accent #FFEA9E, font Montserrat 700) trích từ
 * các màn dropdown/FAB để đồng bộ hình ảnh. `nav` và `slot` đều là prop, nội
 * dung thật do trang cha truyền vào — component không tự biết route hay user.
 */
export function SiteHeader({ appName, nav, slot }: SiteHeaderProps) {
  const t = useCommonUiT();
  return (
    <header
      className={`${montserrat.className} flex flex-wrap items-center justify-between gap-4 border-b border-[#998C5F] bg-[#00101A] px-6 py-4`}
    >
      <span className="text-lg font-bold text-[#FFEA9E]">{appName}</span>
      <nav aria-label={t("siteHeader.navAria")} className="flex flex-wrap items-center gap-6">
        {nav.map((item) => (
          <a
            key={item.href}
            href={item.href}
            aria-current={item.active ? "page" : undefined}
            className={`text-sm font-bold ${
              item.active ? "text-[#FFEA9E]" : "text-white hover:text-[#FFEA9E]"
            }`}
          >
            {item.label}
          </a>
        ))}
      </nav>
      {slot && <div className="flex items-center gap-3">{slot}</div>}
    </header>
  );
}
