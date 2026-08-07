/**
 * Nội dung 6 hạng mục giải "Hệ thống giải thưởng SAA 2025" — **hằng số tĩnh**,
 * không bảng DB (`clarifications.md` gap #10). Đây là nguồn chân lý DUY NHẤT
 * cho cả trang `/awards` (phase-12, file này) lẫn thẻ giải rút gọn ở Homepage
 * (phase-16 sẽ trỏ `HomePageClient` sang đây, xoá `figma-award-mock.ts`).
 *
 * Nguồn: `research/momorph/csv/spec-he-thong-giai-zFYDgyj_pD.csv`, item D.1–D.6,
 * đối chiếu bằng MCP momorph (orchestrator đo trực tiếp node Figma — agent
 * implement phiên này không có MCP khả dụng, xem báo cáo cuối). `title`/
 * `description`/`quantityLabel`/`prizeValueLabel` KHÔNG đi qua i18n — đây là
 * nội dung giải thưởng thật, giữ NGUYÊN VĂN cho mọi locale (giống tên hạng
 * mục không dịch). Chuỗi chrome quanh trang (tiêu đề section, nhãn menu…) mới
 * đi qua `locales/*\/awards.json`.
 */
export interface AwardContent {
  /** kebab-case(title tiếng Việt gốc), dùng cho anchor `/awards#<slug>`. Ghim cứng, không sinh lúc chạy — lý do xem `components/home/figma-award-mock.ts`. */
  slug: string;
  title: string;
  description: string;
  /** Nhãn số lượng đã dựng sẵn, vd "Số lượng giải thưởng: 10 Đơn vị". */
  quantityLabel: string;
  /**
   * Nhãn giá trị giải đã dựng sẵn. Có thể nhiều dòng, ngăn bởi `\n`: dòng đầu
   * mang số tiền, dòng sau là chú thích phụ (vd "cho mỗi giải thưởng"). Riêng
   * Signature có 2 khối giá trị ngăn bởi dòng đúng chữ `"Hoặc"` — `award-card.tsx`
   * (`ValueLines`) nhận diện dòng này để tô kiểu khác. Quy ước dựng chuỗi nằm
   * ở tầng dữ liệu này, KHÔNG đổi hình dạng interface.
   */
  prizeValueLabel: string;
  /** Ảnh chữ tên giải (kênh trong suốt), đặt lên trên `award-bg.png` dùng chung — xem `award-card.tsx`. */
  imageUrl: string;
  /** Thứ tự hiển thị = thứ tự D.1–D.6 trong spec. */
  sortOrder: number;
}

/**
 * **Cập nhật sau khi orchestrator đo lại bằng MCP thật (2026-08-07):** quét cả
 * 72 node TEXT của màn — CHỈ D.1 (Top Talent) và D.5 (Signature 2025 -
 * Creator) có mô tả thật, đã chép nguyên văn dưới đây. D.2/D.3/D.4/D.6 (Top
 * Project, Top Project Leader, Best Manager, MVP) đều là INSTANCE của cùng
 * component D.1 CHƯA ĐƯỢC SỬA NỘI DUNG trong bản thiết kế: tiêu đề, mô tả, số
 * lượng, giá trị của cả 4 đều hiện ra là bản sao y hệt Top Talent — không
 * phải nội dung thật của chúng. Vì vậy 4 mục đó GIỮ NGUYÊN mô tả ngắn đã có từ
 * trước (không chép nhầm đoạn Top Talent vào), số lượng/giá trị lấy từ CSV
 * (nguồn đúng ở màn này cho 2 trường đó, không phải Figma) — **chờ PO cấp mô
 * tả thật**.
 */
export const AWARDS: readonly AwardContent[] = [
  {
    slug: "top-talent",
    title: "Top Talent",
    // Nguyên văn node `I313:8467;214:2531` — đo thật bằng MCP.
    description:
      "Giải thưởng Top Talent vinh danh những cá nhân xuất sắc toàn diện – những người không ngừng khẳng định năng lực chuyên môn vững vàng, hiệu suất công việc vượt trội, luôn mang lại giá trị vượt kỳ vọng, được đánh giá cao bởi khách hàng và đồng đội. Với tinh thần sẵn sàng nhận mọi nhiệm vụ tổ chức giao phó, họ luôn là nguồn cảm hứng, thúc đẩy động lực và tạo ảnh hưởng tích cực đến cả tập thể.",
    quantityLabel: "Số lượng giải thưởng: 10 Đơn vị",
    prizeValueLabel: "Giá trị giải thưởng: 7.000.000 VNĐ\ncho mỗi giải thưởng",
    imageUrl: "/awards/award-top-talent.png",
    sortOrder: 1,
  },
  {
    slug: "top-project",
    // FIXME (thiết kế, không phải code): D.2 là instance chưa sửa nội dung
    // của D.1 trong Figma (tiêu đề/mô tả/số liệu đo được đều là bản sao "Top
    // Talent"/"10"/"7.000.000 VNĐ") — không phải nội dung thật của Top
    // Project. Giữ mô tả ngắn cũ, chờ PO cấp mô tả thật. Số lượng/giá trị lấy
    // từ CSV (D.2: "02 Tập thể" / "15.000.000 VNĐ mỗi giải") vì CSV mới là
    // nguồn đúng cho 2 trường này ở màn này.
    title: "Top Project",
    description: "Vinh danh dự án xuất sắc trên mọi phương diện, dự án có doanh thu nổi bật",
    quantityLabel: "Số lượng giải thưởng: 02 Tập thể",
    prizeValueLabel: "Giá trị giải thưởng: 15.000.000 VNĐ\nmỗi giải",
    imageUrl: "/awards/award-top-project.png",
    sortOrder: 2,
  },
  {
    slug: "top-project-leader",
    // FIXME (thiết kế, không phải code): D.3 cũng là instance chưa sửa của
    // D.1 — mô tả ngắn cũ (dấu phẩy cụt) giữ nguyên, chờ PO cấp nội dung
    // thật. Số lượng/giá trị lấy từ CSV (D.3: "03 Cá nhân" / "7.000.000 VNĐ").
    title: "Top Project Leader",
    description: "Vinh danh người quản lý truyền cảm hứng và dẫn dắt dự án bứt phá,",
    quantityLabel: "Số lượng giải thưởng: 03 Cá nhân",
    prizeValueLabel: "Giá trị giải thưởng: 7.000.000 VNĐ",
    imageUrl: "/awards/award-top-project-leader.png",
    sortOrder: 3,
  },
  {
    slug: "best-manager",
    // FIXME (thiết kế, không phải code): D.4 cũng là instance chưa sửa của
    // D.1 — mô tả ngắn cũ giữ nguyên, chờ PO cấp nội dung thật. Số lượng/giá
    // trị lấy từ CSV (D.4: "01 Cá nhân" / "10.000.000 VNĐ").
    title: "Best Manager",
    description: "Vinh danh người quản lý có năng lực quản lý tốt, dẫn dắt đội nhóm",
    quantityLabel: "Số lượng giải thưởng: 01 Cá nhân",
    prizeValueLabel: "Giá trị giải thưởng: 10.000.000 VNĐ",
    imageUrl: "/awards/award-best-manager.png",
    sortOrder: 4,
  },
  {
    slug: "signature-2025-creator",
    title: "Signature 2025 - Creator",
    // Nguyên văn node `313:8479` — đo thật bằng MCP. Hai khoảng trắng sau dấu
    // chấm đầu câu 2 là NGUYÊN VĂN bản thiết kế, không phải lỗi gõ khi chép.
    description:
      "Giải thưởng Signature vinh danh cá nhân hoặc tập thể thể hiện tinh thần đặc trưng mà Sun* hướng tới trong từng thời kỳ.  Trong năm 2025, giải thưởng Signature vinh danh Creator - cá nhân/tập thể mang tư duy chủ động và nhạy bén, luôn nhìn thấy cơ hội trong thách thức và tiên phong trong hành động. Họ là những người nhạy bén với vấn đề, nhanh chóng nhận diện và đưa ra những giải pháp thực tiễn, mang lại giá trị rõ rệt cho dự án, khách hàng hoặc tổ chức. Với tư duy kiến tạo và tinh thần “Creator” đặc trưng của Sun*, họ không chỉ phản ứng tích cực trước sự thay đổi mà còn chủ động tạo ra cải tiến, góp phần định hình chuẩn mực mới cho cách mà người Sun* tạo giá trị.",
    quantityLabel: "Số lượng giải thưởng: 01",
    // Hai khối giá trị ngăn bởi dòng "Hoặc" — đúng bố cục Figma (khác các thẻ
    // còn lại chỉ có 1 khối).
    prizeValueLabel:
      "Giá trị giải thưởng: 5.000.000 VNĐ\ncho giải cá nhân\nHoặc\n8.000.000 VNĐ\ncho giải tập thể",
    imageUrl: "/awards/award-signature-creator.png",
    sortOrder: 5,
  },
  {
    slug: "mvp",
    // FIXME (thiết kế, không phải code): D.6 cũng là instance chưa sửa của
    // D.1 — mô tả ngắn cũ giữ nguyên, chờ PO cấp nội dung thật. Số lượng/giá
    // trị lấy từ CSV (D.6: "01" / "15.000.000 VNĐ").
    title: "MVP (Most Valuable Person)",
    description: "Vinh danh người quản lý có năng lực quản lý tốt, dẫn dắt đội nhóm",
    quantityLabel: "Số lượng giải thưởng: 01",
    prizeValueLabel: "Giá trị giải thưởng: 15.000.000 VNĐ",
    imageUrl: "/awards/award-mvp.png",
    sortOrder: 6,
  },
] as const;
