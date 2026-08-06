"use client";

import Image from "next/image";

import { SiteFooter } from "@/components/layout/site-footer";
import { buildSiteNav } from "@/components/layout/site-nav";
import { montserrat } from "@/components/ui/fonts";
import { useT } from "@/lib/i18n/locale-provider";

import { useHomeT } from "./use-home-text";

export interface HomeFooterProps {
  /** Mở modal Thể lệ (phase-13) — cùng đích với nút "Thể lệ" trên FAB. */
  onRules: () => void;
}

/**
 * Footer trang chủ (`mms_7_Footer`, node `5001:14800`).
 *
 * Khác footer màn Login dù CÙNG một component Figma: màn này có logo 69×64 và
 * 4 mục nav ở nhóm trái, bản quyền dồn sang phải; màn Login chỉ có dòng bản
 * quyền căn giữa. `SiteFooter` phân biệt bằng việc có truyền `logo`/`nav`/`slot`
 * hay không.
 *
 * Mục thứ 4 "Tiêu chuẩn chung" đi qua `slot` chứ không phải `nav`: nó KHÔNG có
 * route trên bản vẽ, nó mở modal Thể lệ. Render thành `<a href>` là tạo link chết.
 *
 * Bản vẽ gắn trạng thái "đang chọn" (nền `rgba(255,234,158,.1)`) cho mục
 * "Award Information" ở footer, trong khi header lại đánh dấu "About SAA 2025" —
 * hai chỗ mâu thuẫn nhau trên CÙNG một trang. Không chép: `aria-current="page"`
 * đặt lên link trỏ đi trang khác là sai ngữ nghĩa. Đã ghi vào clarifications.
 */
export function HomeFooter({ onRules }: HomeFooterProps) {
  const commonT = useT();
  const t = useHomeT();

  return (
    <SiteFooter
      copyright={commonT("footer.copyright")}
      logo={
        /* mm:I5001:14800;342:1408;178:1030 — 69×64, to hơn logo header (52×48). */
        <Image src="/brand/saa-logo.png" alt={commonT("app.name")} width={69} height={64} />
      }
      nav={buildSiteNav(t)}
      slot={
        <button
          type="button"
          onClick={onRules}
          className={`${montserrat.className} p-4 text-base leading-6 font-bold tracking-[0.15px] text-white transition-colors duration-200 ease-out hover:text-[#FFEA9E] motion-reduce:transition-none`}
        >
          {t("nav.generalCriteria")}
        </button>
      }
    />
  );
}
