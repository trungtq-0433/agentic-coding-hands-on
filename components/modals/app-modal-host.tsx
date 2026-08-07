"use client";

import { useCallback, useRef, useState } from "react";

import { ComposeKudoModal } from "@/components/kudo-compose/compose-kudo-modal";
import type {
  ComposeKudoDraft,
  ComposeKudoSubmitResult,
  Profile,
} from "@/components/kudo-compose/compose-kudo-types";
import { RulesPanel } from "@/components/rules/rules-panel";
import { SecretBoxModal } from "@/components/secret-box/secret-box-modal";
import type { SecretBoxBadge } from "@/components/secret-box/secret-box-types";
import type { HashtagItem } from "@/components/ui/multi-hashtag-picker";

/**
 * Nơi duy nhất mount ba modal của phase-10/13/15.
 *
 * **Vì sao gom về một chỗ:** bốn màn (`/`, `/kudos`, `/profile`, `/awards`) đều
 * có nút mở modal. Nối rời từng màn nghĩa là chép cùng một khối state + cùng bộ
 * prop giả lập ra bốn nơi, rồi phase-16 phải đi sửa cả bốn. Ở đây mỗi màn chỉ
 * giữ đúng một biến `active`, còn toàn bộ dữ liệu và callback nằm gọn một file.
 *
 * **Đây là điểm nối của phase-16.** Mọi thứ dưới đây có tiền tố `MOCK_` hoặc
 * ghi `phase-16` đều phải thay bằng lời gọi thật:
 * - `searchSunners` → truy vấn `profiles` (Track B)
 * - `onSubmit` → Server Action `create_kudos`
 * - `onOpenBox` → RPC `open_secret_box()`
 * Chữ ký giữ nguyên nên khi thay, ba modal không phải sửa dòng nào.
 */

/** Modal đang mở. `null` = không mở cái nào. */
export type AppModal = "compose" | "rules" | "secretBox" | null;

/** Tên Sunner lấy từ chính bản vẽ (cùng danh sách `figma-board-mock.ts`). */
const MOCK_SUNNERS: Profile[] = [
  { id: "mock-user-0", name: "Đỗ hoàng Hiệp", avatarUrl: "/board/avatar-a.png" },
  { id: "mock-user-1", name: "Dương thúy An", avatarUrl: "/board/avatar-b.png" },
  { id: "mock-user-2", name: "Mai phương Thúy", avatarUrl: "/board/avatar-c.png" },
  { id: "mock-user-3", name: "Lê Kiều Trang", avatarUrl: "/board/avatar-a.png" },
  { id: "mock-user-4", name: "Nguyễn Văn Quy", avatarUrl: "/board/avatar-b.png" },
  { id: "mock-user-5", name: "Nguyễn Bá Chức", avatarUrl: "/board/avatar-c.png" },
  { id: "mock-user-6", name: "Nguyễn Hoàng Linh", avatarUrl: "/board/avatar-a.png" },
];

/** Hashtag mang sẵn dấu `#` trong `label` — đúng quy ước `board-page-client.tsx`. */
const MOCK_HASHTAGS: HashtagItem[] = [
  { value: "dedicated", label: "#Dedicated" },
  { value: "inspring", label: "#Inspring" },
];

/** Sáu huy hiệu Secret Box, tên khớp `badges.code` của phase-02. */
const MOCK_BADGES: SecretBoxBadge[] = [
  { name: "Stay Gold", imageUrl: "/rules/badge-stay-gold.png" },
  { name: "Flow to Horizon", imageUrl: "/rules/badge-flow-to-horizon.png" },
  { name: "Beyond the Boundary", imageUrl: "/rules/badge-beyond-the-boundary.png" },
  { name: "Root Further", imageUrl: "/rules/badge-root-further.png" },
  { name: "Touch of Light", imageUrl: "/rules/badge-touch-of-light.png" },
  // Ảnh Revival không tải được (node trả `null` qua hai lần fetch) — để `null`
  // để modal chạy nhánh fallback chữ, đúng như khi server không có ảnh.
  { name: "Revival", imageUrl: null },
];

/** Độ trễ giả lập, đủ để nhìn thấy trạng thái "đang gửi"/"đang mở". */
const MOCK_LATENCY_MS = 500;

export interface AppModalHostProps {
  active: AppModal;
  /**
   * Đổi modal đang mở. `null` = đóng hết.
   *
   * Nhận HÀM ĐỔI chứ không chỉ `onClose` vì các modal có đường đi lẫn nhau:
   * panel Thể lệ có nút "Viết KUDOS" phải chuyển thẳng sang modal soạn Kudo.
   * Nếu chỉ có `onClose` thì nút đó không có cách nào mở modal khác — bản đầu
   * của file này truyền `onCompose={() => undefined}` và nút thành nút chết.
   */
  onChange: (modal: AppModal) => void;
  /** Pre-fill người nhận khi mở từ profile người khác (TC_WEB_PROFILE_FUN_007). */
  presetRecipient?: Profile | null;
  /** Số Secret Box chưa mở — màn nào có số thật thì truyền vào. */
  unopenedBoxes?: number;
}

export function AppModalHost({
  active,
  onChange,
  presetRecipient = null,
  unopenedBoxes = 25,
}: AppModalHostProps) {
  /**
   * Modal xếp hàng mở NGAY SAU khi cái đang mở đóng lại.
   *
   * Cần vì `RulesPanel` gọi `onCompose()` RỒI `onClose()` ngay trong cùng một
   * handler (đúng hợp đồng phase-13: "gọi onCompose và đóng panel"). Nếu cả hai
   * cùng gọi thẳng `onChange`, lệnh đóng ghi đè lệnh mở và kết quả là KHÔNG
   * modal nào mở — đã kiểm bằng cách bấm thật, ra `soModal: 0`.
   * Xếp hàng ở đây để `close()` biết nên đóng hẳn hay chuyển tiếp.
   */
  const nextRef = useRef<AppModal>(null);
  const close = useCallback(() => {
    const next = nextRef.current;
    nextRef.current = null;
    onChange(next);
  }, [onChange]);
  const [submitting, setSubmitting] = useState(false);
  const [remaining, setRemaining] = useState(unopenedBoxes);
  const [lastBadge, setLastBadge] = useState<SecretBoxBadge | null>(null);
  const [opening, setOpening] = useState(false);
  /* Đếm số lần đã mở để chọn huy hiệu tất định. KHÔNG `Math.random()`: cùng lý
     do như mọi mock khác trong dự án — giá trị đổi mỗi render sẽ làm server và
     client dựng khác nhau. Random thật là việc của RPC (trọng số 30/25/10/5/20/10). */
  const openCountRef = useRef(0);

  const searchSunners = useCallback(async (query: string): Promise<Profile[]> => {
    const q = query.trim().toLowerCase();
    if (!q) return [];
    return MOCK_SUNNERS.filter((s) => s.name.toLowerCase().includes(q));
  }, []);

  const handleSubmit = useCallback(
    (draft: ComposeKudoDraft): Promise<ComposeKudoSubmitResult> => {
      setSubmitting(true);
      return new Promise<ComposeKudoSubmitResult>((resolve) => {
        window.setTimeout(() => {
          // phase-16: gọi Server Action `create_kudos` và trả `fieldErrors` thật.
          console.info("[modal-host] draft kudo (chưa gửi đi đâu):", draft);
          setSubmitting(false);
          resolve({ ok: true });
        }, MOCK_LATENCY_MS);
      });
    },
    [],
  );

  const handleOpenBox = useCallback((): Promise<{ badge: SecretBoxBadge; remaining: number }> => {
    setOpening(true);
    return new Promise((resolve) => {
      window.setTimeout(() => {
        // phase-16: RPC `open_secret_box()`. Số trả về là của SERVER, modal chỉ
        // hiển thị — chỗ trừ đi 1 nằm ở đây (cha), không nằm trong modal.
        const badge = MOCK_BADGES[openCountRef.current % MOCK_BADGES.length];
        openCountRef.current += 1;
        setRemaining((prev) => {
          const next = Math.max(0, prev - 1);
          setLastBadge(badge);
          setOpening(false);
          resolve({ badge, remaining: next });
          return next;
        });
      }, MOCK_LATENCY_MS);
    });
  }, []);

  return (
    <>
      <ComposeKudoModal
        open={active === "compose"}
        onClose={close}
        onSubmit={handleSubmit}
        searchSunners={searchSunners}
        hashtags={MOCK_HASHTAGS}
        presetRecipient={presetRecipient}
        submitting={submitting}
        errors={{}}
      />
      {/* Thể lệ → Viết Kudo: xếp hàng "compose" rồi để panel tự đóng, `close()`
          sẽ chuyển tiếp sang modal soạn thay vì đóng về trang trắng. */}
      <RulesPanel
        open={active === "rules"}
        onClose={close}
        onCompose={() => {
          nextRef.current = "compose";
        }}
      />
      <SecretBoxModal
        open={active === "secretBox"}
        onClose={close}
        onOpenBox={handleOpenBox}
        remaining={remaining}
        lastBadge={lastBadge}
        opening={opening}
      />
    </>
  );
}
