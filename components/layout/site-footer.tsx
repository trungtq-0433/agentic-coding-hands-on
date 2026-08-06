"use client";

import type { ReactNode } from "react";

import { montserrat, montserratAlternates } from "@/components/ui/fonts";
import { useCommonUiT } from "@/components/ui/use-common-ui-text";

import type { NavItem } from "./site-header";

export interface SiteFooterProps {
  /** Chuỗi bản quyền đã dịch — thuộc namespace `common.json` (phase-01 sở hữu), trang cha truyền vào. */
  copyright: string;
  /**
   * Logo thương hiệu ở nhóm bên trái. Bàn giao kiểm soát phase-06 → phase-08:
   * footer màn Homepage (`5001:14800`) có logo 69×64 + 4 mục nav, trong khi màn
   * Login chỉ có dòng bản quyền căn giữa — cùng một component Figma, hai cách
   * dùng. Đối xứng với `SiteHeader.logo` đã có sẵn.
   */
  logo?: ReactNode;
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
export function SiteFooter({ copyright, logo, nav, slot }: SiteFooterProps) {
  const t = useCommonUiT();
  const hasSides =
    logo !== undefined || (nav !== undefined && nav.length > 0) || slot !== undefined;
  return (
    <footer
      className={`${montserratAlternates.className} mt-auto flex flex-wrap items-center gap-6 border-t border-[#2E3940] bg-[#00101A] px-6 py-10 md:px-[90px] ${
        hasSides ? "justify-between" : "justify-center"
      }`}
    >
      {/* Nhóm TRÁI: logo → nav → slot, đúng thứ tự `Frame 488` của Figma
          (`I5001:14800;342:1407`): logo cách nav 80px, các mục nav cách nhau 48px.
          Dòng bản quyền nằm bên PHẢI. Màn `/login` không truyền logo/nav/slot nên
          `hasSides` sai → chỉ còn dòng bản quyền căn giữa, giữ nguyên như cũ. */}
      {hasSides && (
        <div className="flex flex-wrap items-center gap-8 lg:gap-20">
          {logo}
          {nav && nav.length > 0 && (
            <nav
              aria-label={t("siteFooter.navAria")}
              className={`${montserrat.className} flex flex-wrap items-center gap-6 lg:gap-12`}
            >
              {nav.map((item) => (
                <a
                  key={item.href}
                  href={item.href}
                  aria-current={item.active ? "page" : undefined}
                  className="p-4 text-base leading-6 font-bold tracking-[0.15px] text-white transition-colors duration-200 ease-out hover:text-[#FFEA9E] motion-reduce:transition-none"
                >
                  {item.label}
                </a>
              ))}
            </nav>
          )}
          {slot}
        </div>
      )}
      <p className="text-center text-base leading-6 font-bold text-white">{copyright}</p>
    </footer>
  );
}
