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
  /**
   * Logo thương hiệu. Truyền vào thì render ảnh thật thay cho chữ `appName`
   * (chữ chỉ là dự phòng khi trang chưa có asset logo).
   */
  logo?: ReactNode;
  /** Vùng bên phải header do trang cha bơm vào (AccountMenu, LanguageSwitcher, nút đăng nhập...). */
  slot?: ReactNode;
}

/**
 * Chrome header dùng chung — dựng theo ĐÚNG component Figma `mms_A_Header`
 * (`186:1602`, đo trên màn Login `GzbNeVGJHz`), không phải theo suy đoán:
 *
 *   height 80px · padding 12px 144px · justify-content space-between
 *   background rgba(11,15,18,0.8)  ← TRONG SUỐT, phủ lên hoạ tiết hero
 *   KHÔNG có border-bottom
 *
 * Bản đầu (phase-06) dựng khi chưa có màn nào chứa header nên phải suy từ token
 * của các màn dropdown/FAB: nền đặc `#00101A`, viền `#998C5F`, chữ thay logo.
 * Màn Login mang header thật nên đã thay bằng số đo gốc.
 *
 * `nav`, `logo`, `slot` đều là prop — component không tự biết route hay user.
 */
export function SiteHeader({ appName, nav, logo, slot }: SiteHeaderProps) {
  const t = useCommonUiT();
  return (
    <header
      className={`${montserrat.className} flex h-20 flex-wrap items-center justify-between gap-4 bg-[rgba(11,15,18,0.8)] px-6 py-3 md:px-16 lg:px-36`}
    >
      {logo ?? <span className="text-lg font-bold text-[#FFEA9E]">{appName}</span>}
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
