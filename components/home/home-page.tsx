"use client";

import Image from "next/image";
import { useRouter } from "next/navigation";

import { buildSiteNav, SITE_NAV_HREFS } from "@/components/layout/site-nav";
import type { AccountMenuProfile } from "@/components/ui/account-menu";
import { KudosFab } from "@/components/ui/kudos-fab";
import { LOCALE_COOKIE, type Locale } from "@/lib/i18n/config";
import { useLocale } from "@/lib/i18n/locale-provider";

import type { AwardCardData } from "./award-card";
import { AwardSection } from "./award-section";
import { HomeFooter } from "./home-footer";
import { HomeHeader } from "./home-header";
import { HomeHero } from "./home-hero";
import { RootFurtherSection } from "./root-further-section";
import { SunKudosSection } from "./sun-kudos-section";
import { useHomeT } from "./use-home-text";

export interface HomePageProps {
  /** ISO datetime mốc sự kiện — nguồn là `NEXT_PUBLIC_EVENT_START_AT`, trang cha đọc. */
  targetIso: string;
  /** 6 hạng mục giải, nội dung tĩnh do phase-12 sở hữu (phase-08 chỉ render). */
  awards: AwardCardData[];
  /** `null` = khách chưa đăng nhập. Guest xem được TOÀN BỘ nội dung, không chặn gì ở UI. */
  profile: AccountMenuProfile | null;
  isAdmin: boolean;
  onCompose: () => void;
  onRules: () => void;
  onSignOut: () => void;
}

/**
 * Trang chủ SAA 2025 — Figma frame `Homepage SAA` (`2167:9026`, screenId
 * `i87tDx10uM`). Track A / phase-08: không import `lib/data|actions|supabase`,
 * mọi hành vi động đi qua props.
 *
 * Bố cục dọc bám đúng toạ độ Figma của khung `Bìa` (`2167:9030`):
 * `padding 96px 144px`, `gap 120px` giữa 4 khối nội dung. Các khối con KHÔNG tự
 * thêm padding dọc (trừ Root Further vốn có `padding 120px` riêng trên bản vẽ) —
 * nếu khối nào cũng tự đệm thì khoảng cách thực tế thành gần gấp đôi 120px.
 *
 * Kiểm chứng bằng toạ độ: Bìa mở ở y=88, +96 padding → Frame 487 tại y=184 ✓;
 * Frame 487 đóng ở 779, +120 → Root Further tại 899 ✓; đóng 2118, +120 → lưới
 * giải tại 2238 ✓; đóng 3591, +120 → Sun* Kudos tại 3711 ✓; đóng 4211, +96
 * padding → Bìa đóng ở 4307 ✓.
 */
export function HomePage({
  targetIso,
  awards,
  profile,
  isAdmin,
  onCompose,
  onRules,
  onSignOut,
}: HomePageProps) {
  const locale = useLocale();
  const t = useHomeT();
  const router = useRouter();

  function handleLocaleChange(next: Locale) {
    if (next === locale) return;
    document.cookie = `${LOCALE_COOKIE}=${next}; path=/; max-age=31536000; SameSite=Lax`;
    router.refresh();
  }

  return (
    // mm:2167:9026 — nền `#00101A`. `isolate` để hai lớp nền z âm bên dưới
    // nằm gọn trong stacking context của trang.
    //
    // KHÔNG thêm `overflow-x-hidden` vào đây. Đã thử và trang mất sạch nền
    // keyvisual: CSS quy định khi một trục `overflow` là `hidden` còn trục kia
    // `visible` thì trục `visible` bị tính lại thành `auto` — thẻ này trở thành
    // vùng cuộn, và Chromium sơn nền của vùng cuộn vào lớp nội dung cuộn, tức
    // ĐÈ LÊN các con z âm. Ảnh vẫn load, vẫn `opacity:1`, vẫn đúng kích thước,
    // chỉ là không bao giờ nhìn thấy. `/login` dùng cùng khuôn z âm mà không
    // dính vì nó `overflow-hidden` cả hai trục (không sinh ra `auto`).
    // Hai lớp nền đều `inset-x-0` nên không tràn ngang — không cần cắt.
    <div className="relative isolate flex min-h-full flex-1 flex-col bg-[#00101A]">
      {/* mm:2167:9027 — keyvisual 1512×1392, trải từ đỉnh trang xuống TẬN SAU
          khối Root Further (không chỉ sau hero). Chiều cao giữ đúng tỉ lệ ảnh
          92.06vw = 1392/1512, chặn trên ở 1392px để màn siêu rộng không kéo dài
          vô hạn. `next/image` chứ không `background-image`: file gốc 4,3MB, để
          CSS tải thì trình duyệt lấy nguyên bản không qua tối ưu định dạng. */}
      <div aria-hidden="true" className="pointer-events-none absolute inset-x-0 top-0 -z-20 h-[92.06vw] max-h-[1392px]">
        <Image src="/home/keyvisual-bg.png" alt="" fill priority sizes="100vw" className="object-cover object-top" />
      </div>
      {/* mm:2167:9029 — lớp phủ Cover 1512×1480 (cao hơn keyvisual 88px, để
          hoạ tiết tan hẳn vào nền trước khi hết). */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-x-0 top-0 -z-10 h-[97.88vw] max-h-[1480px]"
        style={{
          background:
            "linear-gradient(12deg, #00101A 23.7%, rgba(0,18,29,0.46) 38.34%, rgba(0,19,32,0) 48.92%)",
        }}
      />

      {/* mm:2167:9091 — header PHỦ LÊN keyvisual (nền rgba(11,15,18,.8)).
          Chỉ phủ từ `lg` trở lên: bản vẽ chỉ tồn tại ở khung 1512px, nơi header
          vừa đúng một hàng 80px. Ở màn hẹp, logo + 3 mục nav + bộ chọn ngôn ngữ
          + chuông + nút đăng nhập buộc phải xuống dòng; header phủ mà cao lên
          thì nó che mất chữ hero (đã thấy ở 375px). Dưới `lg` cho header nằm
          trong luồng, đẩy nội dung xuống — Figma không có khung mobile cho màn
          này nên đây là quyết định của bản dựng, đã ghi vào clarifications. */}
      <div className="relative z-20 lg:absolute lg:inset-x-0 lg:top-0">
        <HomeHeader
          locale={locale}
          nav={buildSiteNav(t, SITE_NAV_HREFS.home)}
          profile={profile}
          isAdmin={isAdmin}
          onLocaleChange={handleLocaleChange}
          onProfile={() => router.push("/profile")}
          onAdmin={() => router.push("/admin")}
          onSignOut={onSignOut}
        />
      </div>

      {/* mm:2167:9030 `Bìa` — padding 96px 144px, gap 120px */}
      {/* `lg:pt-[184px]` = 88px (mép trên `Bìa`) + 96px (padding trên) — chừa
          đúng chỗ cho header phủ. Dưới `lg` header đã nằm trong luồng nên chỉ
          cần đệm thường. */}
      <main className="mx-auto flex w-full max-w-[1512px] flex-col gap-16 px-6 pt-12 pb-16 md:px-16 lg:gap-[120px] lg:px-36 lg:pt-[184px] lg:pb-24">
        <HomeHero
          targetIso={targetIso}
          onAboutAwards={() => router.push("/awards")}
          onAboutKudos={() => router.push("/kudos")}
        />
        <RootFurtherSection />
        <AwardSection awards={awards} onAwardDetail={(slug) => router.push(`/awards#${slug}`)} />
        <SunKudosSection onDetail={() => router.push("/kudos")} />
      </main>

      {/* mm:5022:15169 — FAB. Figma vẽ nó `absolute top:830 right:19` trong khung
          bản vẽ vì artboard không diễn tả được `position: fixed`; `KudosFab`
          (phase-06) dùng `fixed bottom-8 right-5`, khớp mép phải 19px≈20px. */}
      <KudosFab onRules={onRules} onCompose={onCompose} />

      {/* mm:5001:14800 */}
      <HomeFooter onRules={onRules} />
    </div>
  );
}
