import { cookies } from "next/headers";

import { DEFAULT_LOCALE, isLocale, LOCALE_COOKIE, type Locale } from "./config";

/**
 * Nạp dictionary phía server, theo namespace.
 *
 * Mỗi phase Track A sở hữu namespace JSON riêng dưới `locales/{locale}/{namespace}.json`
 * (common, common-ui, login, profile…) — không hai phase nào ghi cùng một file.
 * Loader dùng `import()` với template literal nên KHÔNG cần sửa file này mỗi khi
 * một phase mới thêm namespace của riêng nó — chỉ cần tạo file JSON tương ứng
 * trong `locales/{locale}/`.
 *
 * Vì sao `import()` chứ không phải `fs.readFile(process.cwd() + …)`: bundler
 * (Turbopack) phân tích tĩnh được mẫu đường dẫn này và gói SẴN mọi file khớp
 * `locales/*\/*.json` vào output. Đọc đĩa lúc runtime thì dictionary nằm ngoài
 * bundle và phụ thuộc `process.cwd()` — chạy được với `next start` tại chỗ,
 * nhưng gãy với `output: 'standalone'` hoặc serverless. Cách này không đánh đổi
 * tính tổng quát để lấy điều đó.
 */
export type Dictionary = Record<string, string>;

/** Namespace mặc định — giữ nguyên chữ ký `getDictionary(locale)` mà `app/layout.tsx` (phase-01) đang gọi. */
const DEFAULT_NAMESPACE = "common";

/** Đọc locale từ cookie NEXT_LOCALE; giá trị lạ hoặc thiếu → DEFAULT_LOCALE. */
export async function getLocale(): Promise<Locale> {
  const value = (await cookies()).get(LOCALE_COOKIE)?.value;
  return isLocale(value) ? value : DEFAULT_LOCALE;
}

/**
 * Nạp dictionary cho một namespace bất kỳ. Namespace luôn là hằng chuỗi do code
 * gọi (không phải input người dùng), nhưng nội dung file JSON trên đĩa vẫn là dữ
 * liệu đến từ ngoài type-system — được validate ở `validateDictionary` trước khi
 * trả về, thay vì tin suông vào phần mở rộng `.json`.
 */
export async function getDictionary(
  locale: Locale,
  namespace: string = DEFAULT_NAMESPACE,
): Promise<Dictionary> {
  return loadDictionary(locale, namespace);
}

/**
 * Không tự cache: `import()` đã được module system giữ sẵn kết quả, bọc thêm một
 * Map<Promise> chỉ thêm mã cần bảo trì mà không nhanh hơn.
 */
async function loadDictionary(locale: Locale, namespace: string): Promise<Dictionary> {
  let parsed: unknown;
  try {
    parsed = (await import(`../../locales/${locale}/${namespace}.json`)).default;
  } catch (cause) {
    throw new Error(
      `Không nạp được dictionary namespace "${namespace}" cho locale "${locale}" ` +
        `(locales/${locale}/${namespace}.json)`,
      { cause },
    );
  }

  return validateDictionary(parsed, locale, namespace);
}

/** Boundary check: JSON có thể do phase khác thêm vào — vẫn kiểm hình dạng object phẳng { key: string }. */
function validateDictionary(value: unknown, locale: Locale, namespace: string): Dictionary {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new Error(`Dictionary namespace "${namespace}"/${locale} phải là object phẳng { key: string }`);
  }
  for (const [key, entry] of Object.entries(value as Record<string, unknown>)) {
    if (typeof entry !== "string") {
      throw new Error(
        `Dictionary namespace "${namespace}"/${locale} có giá trị không phải string tại key "${key}"`,
      );
    }
  }
  return value as Dictionary;
}
