"use client";

import Image from "next/image";
import { useRouter } from "next/navigation";

import { SiteHeader } from "@/components/layout/site-header";
import { SiteFooter } from "@/components/layout/site-footer";
import { LanguageSwitcher } from "@/components/ui/language-switcher";
import { montserrat } from "@/components/ui/fonts";
import { useLocale, useT } from "@/lib/i18n/locale-provider";
import { LOCALE_COOKIE, type Locale } from "@/lib/i18n/config";

import { useLoginT } from "./use-login-text";

export interface LoginScreenProps {
  onGoogleLogin: () => void;
  errorCode?: "oauth";
}

/**
 * Màn `/login` (Figma frame `662:14387`). Header/Footer KHÔNG dựng lại — compose
 * `SiteHeader`/`SiteFooter` dùng chung (phase-06). Ảnh nền sóng của hero
 * (node `662:14389`, tên "image 1" — KHÔNG có tiền tố `mm_media_`) không lấy
 * được: không có URL trong `get_media_files` và `get_figma_image` fallback trả
 * 500 hai lần liên tiếp. Thay bằng nền đặc `#00101A` — cùng tông màu 2 lớp
 * gradient phủ thật (`662:14392`, `662:14390`) nên không lệch bố cục, chỉ thiếu
 * chi tiết hoạ tiết sóng. Xem báo cáo cuối phase để theo dõi việc bổ sung asset
 * này khi Figma export lại được.
 */
export function LoginScreen({ onGoogleLogin, errorCode }: LoginScreenProps) {
  const locale = useLocale();
  const commonT = useT();
  const t = useLoginT();
  const router = useRouter();

  function handleLocaleChange(next: Locale) {
    if (next === locale) return;
    document.cookie = `${LOCALE_COOKIE}=${next}; path=/; max-age=31536000; SameSite=Lax`;
    router.refresh();
  }

  return (
    // mm:662:14387
    <div className="relative flex min-h-full flex-1 flex-col">
      {/* mm:662:14391 — header PHỦ LÊN hero (Figma: position absolute, nền
          rgba(11,15,18,.8)), không xếp chồng phía trên. Logo là asset thật
          MM_MEDIA_Logo 52x48, không phải chữ. */}
      <div className="absolute inset-x-0 top-0 z-20">
        <SiteHeader
          appName={commonT("app.name")}
          nav={[]}
          logo={
            /* mm:I662:14391;178:1033;178:1030 */
            <Image
              src="/brand/saa-logo.png"
              alt={commonT("app.name")}
              width={52}
              height={48}
              priority
            />
          }
          slot={<LanguageSwitcher locale={locale} onChange={handleLocaleChange} />}
        />
      </div>

      <section className="relative isolate flex flex-1 flex-col overflow-hidden bg-[#00101A] pt-20">
        {/* mm:662:14388 — nền hero.
            TẠM THỜI: node ảnh gốc `662:14389` tên "image 1" — KHÔNG có tiền tố
            `MM_MEDIA_` nên nằm ngoài pipeline asset của MoMorph, và đường thoát
            `get_figma_image` trả 500 ở mọi biến thể (kể cả trên node đã có URL
            S3, nên là lỗi endpoint chứ không phải lỗi node). Ảnh dưới đây là
            vùng hoạ tiết cắt từ `get_frame_image` — pixel THẬT của thiết kế,
            nhưng nguồn là ảnh render 1440px nên màn rộng hơn sẽ mềm nét, và
            thiếu phần hoạ tiết bên trái nơi chữ đè lên.
            ĐỂ ĐẠT 100%: đổi tên node `662:14389` thành `MM_MEDIA_Hero` trong
            Figma → `get_media_files` sẽ trả URL S3 → thay đúng file này. */}
        <div aria-hidden="true" className="absolute inset-0 -z-20 bg-[#00101A]" />
        <div
          aria-hidden="true"
          className="absolute inset-y-0 right-0 -z-20 w-[62%] bg-[url('/login/hero-waves-interim.jpg')] bg-cover bg-right bg-no-repeat"
          /* Mép trái của crop là chỗ cắt, không phải chỗ hoạ tiết kết thúc thật —
             để trần sẽ thấy một đường nối dọc. Mask cho nó tan dần vào nền như
             thiết kế gốc (hoạ tiết chìm dưới lớp gradient chứ không bị cắt). */
          style={{
            maskImage: "linear-gradient(to right, transparent 0%, black 22%)",
            WebkitMaskImage: "linear-gradient(to right, transparent 0%, black 22%)",
          }}
        />
        {/* mm:662:14392 — gradient trái sang phải */}
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-0 -z-10 bg-gradient-to-r from-[#00101A] via-[#00101A] to-transparent"
        />

        <div className="flex flex-1 flex-col justify-center gap-10 px-6 py-12 sm:px-10 md:gap-16 md:px-16 md:py-16 lg:gap-[120px] lg:px-36 lg:py-24">
          <div className="flex flex-col items-start gap-10 lg:w-[1152px] lg:gap-20">
            {/* mm:662:14395 */}
            <div className="flex flex-col items-start gap-6">
              {/* mm:2939:9548 */}
              <Image
                src="/login/Root_Further_Logo.png"
                alt={t("hero.title")}
                width={451}
                height={200}
                priority
                className="h-auto w-full max-w-[280px] sm:max-w-[360px] lg:max-w-[451px]"
              />
            </div>

            {/* mm:662:14755 */}
            <div className="flex flex-col items-start gap-6 pl-0 md:pl-4">
              {errorCode === "oauth" && (
                <div
                  role="alert"
                  className={`${montserrat.className} rounded-lg border border-red-400 bg-red-950/60 px-4 py-3 text-sm font-bold text-red-100`}
                >
                  {t("error.oauth")}
                </div>
              )}

              {/* mm:662:14753 */}
              <p className={`${montserrat.className} max-w-[480px] text-lg font-bold leading-8 tracking-[0.5px] text-white lg:text-xl lg:leading-10`}>
                {t("hero.subtitle")}
                <br />
                {t("hero.tagline")}
              </p>

              {/* mm:662:14425 */}
              <div className="flex flex-row items-center gap-10">
                {/* mm:662:14426 */}
                <button
                  type="button"
                  onClick={onGoogleLogin}
                  className={`${montserrat.className} inline-flex items-center gap-2 rounded-lg bg-[#FFEA9E] px-5 py-3 text-lg font-bold text-[#00101A] transition-colors duration-200 ease-out hover:bg-[#ffe17a] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FFEA9E] lg:px-6 lg:py-4 lg:text-[22px]`}
                >
                  {/* mm:I662:14426;186:1935 mm:I662:14426;186:1568 */}
                  <span>{t("action.loginWithGoogle")}</span>
                  {/* mm:I662:14426;186:1766 */}
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden="true" xmlns="http://www.w3.org/2000/svg">
                    <path d="M20.8245 12.2073C20.8245 11.5955 20.7748 10.9804 20.669 10.3785H12.1799V13.8443H17.0412C16.8395 14.962 16.1913 15.9508 15.2422 16.5792V18.8279H18.1425C19.8456 17.2604 20.8245 14.9455 20.8245 12.2073Z" fill="#4285F4" />
                    <path d="M12.1799 21.0006C14.6073 21.0006 16.6543 20.2036 18.1458 18.8279L15.2455 16.5792C14.4386 17.1281 13.3969 17.439 12.1832 17.439C9.83527 17.439 7.84445 15.8549 7.13014 13.7252H4.1373V16.0434C5.66514 19.0826 8.77703 21.0006 12.1799 21.0006Z" fill="#34A853" />
                    <path d="M7.12684 13.7252C6.74984 12.6074 6.74984 11.3971 7.12684 10.2793V7.96112H4.13731C2.86081 10.5042 2.8608 13.5003 4.1373 16.0434L7.12684 13.7252Z" fill="#FBBC04" />
                    <path d="M12.1799 6.56224C13.463 6.5424 14.7032 7.02523 15.6324 7.9115L18.202 5.34196C16.5749 3.81413 14.4155 2.97415 12.1799 3.00061C8.77702 3.00061 5.66515 4.91868 4.13731 7.96112L7.12684 10.2793C7.83785 8.14631 9.83196 6.56224 12.1799 6.56224Z" fill="#EA4335" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* mm:662:14390 — gradient dưới lên trên */}
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-x-0 bottom-0 -z-10 h-1/2 bg-gradient-to-t from-[#00101A] to-transparent"
        />
      </section>

      {/* mm:662:14447 */}
      <SiteFooter copyright={commonT("footer.copyright")} />
    </div>
  );
}
