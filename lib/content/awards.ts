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
 * **Đính chính (2026-08-07, lần hai).** Bản ghi trước ở đây khẳng định
 * D.2/D.3/D.4/D.6 là instance CHƯA SỬA NỘI DUNG trong bản thiết kế, và giữ mô
 * tả ngắn cho bốn thẻ đó kèm FIXME "chờ PO". **Khẳng định đó SAI, do đọc nhầm
 * trường dữ liệu.**
 *
 * `query_by_type` chỉ trả `itemName` — là TÊN node Figma, vốn được đặt theo nội
 * dung LÚC TẠO và KHÔNG đổi khi người ta sửa chữ. Nội dung thật nằm ở trường
 * `character`, mà lệnh đó không trả về. Ví dụ node `I313:8468;214:2622` có
 * `itemName: "Top Talent"` nhưng `character: "Top Project"`.
 *
 * Đã kiểm lại từng node bằng `get_node`/`query_section` (hai lệnh CÓ trả
 * `character`): **cả 6 thẻ đều có tiêu đề, mô tả, số lượng và giá trị riêng.**
 * Toàn bộ nội dung dưới đây là nguyên văn `character` của các node tương ứng;
 * số lượng/giá trị đối chiếu thêm bằng ảnh thiết kế.
 *
 * Bài học: `itemName` KHÔNG phải nội dung. Muốn đọc chữ thì dùng `character`.
 */
export const AWARDS: readonly AwardContent[] = [
  {
    slug: "top-talent",
    title: "Top Talent",
    // Nguyên văn node `I313:8467;214:2531` — đo thật bằng MCP.
    description:
      "Giải thưởng Top Talent vinh danh những cá nhân xuất sắc toàn diện – những người không ngừng khẳng định năng lực chuyên môn vững vàng, hiệu suất công việc vượt trội, luôn mang lại giá trị vượt kỳ vọng, được đánh giá cao bởi khách hàng và đồng đội. Với tinh thần sẵn sàng nhận mọi nhiệm vụ tổ chức giao phó, họ luôn là nguồn cảm hứng, thúc đẩy động lực và tạo ảnh hưởng tích cực đến cả tập thể.",
    quantityLabel:
      "Số lượng giải thưởng: 10 Cá nhân",
    prizeValueLabel: "Giá trị giải thưởng: 7.000.000 VNĐ\ncho mỗi giải thưởng",
    imageUrl: "/awards/award-top-talent.png",
    sortOrder: 1,
  },
  {
    slug: "top-project",
    title: "Top Project",
    description:
      "Giải thưởng Top Project vinh danh các tập thể dự án xuất sắc với kết quả kinh doanh vượt kỳ vọng, hiệu quả vận hành tối ưu và tinh thần làm việc tận tâm. Đây là các dự án có độ phức tạp kỹ thuật cao, hiệu quả tối ưu hóa nguồn lực và chi phí tốt, đề xuất các ý tưởng có giá trị cho khách hàng, đem lại lợi nhuận vượt trội và nhận được phản hồi tích cực từ khách hàng. Các thành viên tuân thủ nghiêm ngặt các tiêu chuẩn phát triển nội bộ trong phát triển dự án, tạo nên một hình mẫu về sự xuất sắc và chuyên nghiệp.",
    quantityLabel: "Số lượng giải thưởng: 02 Tập thể",
    prizeValueLabel:
      "Giá trị giải thưởng: 15.000.000 VNĐ\ncho mỗi giải thưởng",
    imageUrl: "/awards/award-top-project.png",
    sortOrder: 2,
  },
  {
    slug: "top-project-leader",
    title: "Top Project Leader",
    description:
      "Giải thưởng Top Project Leader vinh danh những nhà quản lý dự án xuất sắc – những người hội tụ năng lực quản lý vững vàng, khả năng truyền cảm hứng mạnh mẽ, và tư duy “Aim High – Be Agile” trong mọi bài toán và bối cảnh. Dưới sự dẫn dắt của họ, các thành viên không chỉ cùng nhau vượt qua thử thách và đạt được mục tiêu đề ra, mà còn giữ vững ngọn lửa nhiệt huyết, tinh thần Wasshoi, và trưởng thành để trở thành phiên bản tinh hoa – hạnh phúc hơn của chính mình.",
    quantityLabel: "Số lượng giải thưởng: 03 Cá nhân",
    prizeValueLabel:
      "Giá trị giải thưởng: 7.000.000 VNĐ\ncho mỗi giải thưởng",
    imageUrl: "/awards/award-top-project-leader.png",
    sortOrder: 3,
  },
  {
    slug: "best-manager",
    title: "Best Manager",
    description:
      "Giải thưởng Best Manager vinh danh những nhà lãnh đạo tiêu biểu – người đã dẫn dắt đội ngũ của mình tạo ra kết quả vượt kỳ vọng, tác động nổi bật đến hiệu quả kinh doanh và sự phát triển bền vững của tổ chức. Dưới sự lãnh đạo của họ, đội ngũ luôn chinh phục và làm chủ mọi mục tiêu bằng năng lực đa nhiệm, khả năng phối hợp hiệu quả, và tư duy ứng dụng công nghệ linh hoạt trong kỷ nguyên số. Họ truyền cảm hứng để tập thể trở nên tự tin tràn đầy năng lượng, sẵn sàng đón nhận, thậm chí dẫn dắt tạo ra những thay đổi có tính cách mạng.",
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
    quantityLabel:
      "Số lượng giải thưởng: 01 Cá nhân hoặc tập thể",
    // Hai khối giá trị ngăn bởi dòng "Hoặc" — đúng bố cục Figma (khác các thẻ
    // còn lại chỉ có 1 khối).
    prizeValueLabel:
      "Giá trị giải thưởng: 5.000.000 VNĐ\ncho giải cá nhân\nHoặc\n8.000.000 VNĐ\ncho giải tập thể",
    imageUrl: "/awards/award-signature-creator.png",
    sortOrder: 5,
  },
  {
    slug: "mvp",
    title: "MVP (Most Valuable Person)",
    description:
      "Giải thưởng MVP vinh danh cá nhân xuất sắc nhất năm – gương mặt tiêu biểu đại diện cho toàn bộ tập thể Sun*. Họ là người đã thể hiện năng lực vượt trội, tinh thần cống hiến bền bỉ, và tầm ảnh hưởng sâu rộng, để lại dấu ấn mạnh mẽ trong hành trình của Sun* suốt năm qua. Không chỉ nổi bật bởi hiệu suất và kết quả công việc, họ còn là nguồn cảm hứng lan tỏa – thông qua suy nghĩ, hành động và ảnh hưởng tích cực của mình đối với tập thể. MVP là người hội tụ đầy đủ phẩm chất của người Sun* ưu tú, đồng thời mang trên mình trọng trách lớn lao: trở thành hình mẫu đại diện cho con người và tinh thần Sun*, góp phần dẫn dắt tập thể vươn tới những đỉnh cao mới.",
    quantityLabel:
      "Số lượng giải thưởng: 01 Cá nhân",
    prizeValueLabel: "Giá trị giải thưởng: 15.000.000 VNĐ",
    imageUrl: "/awards/award-mvp.png",
    sortOrder: 6,
  },
] as const;
