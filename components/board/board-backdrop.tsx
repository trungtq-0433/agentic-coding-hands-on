import Image from "next/image";

/**
 * Hai lớp nền đầu màn Live board — `Keyvisual` (`2940:13432`) và lớp `Cover`
 * tối dần phủ lên nó.
 *
 * Ảnh cao 512px trên khung 1440px → tỉ lệ 35.6vw; chặn trên ở 512px để màn siêu
 * rộng không kéo dài vô hạn.
 *
 * `next/image` chứ không `background-image`: CSS tải nguyên bản không qua tối ưu
 * định dạng.
 *
 * **Cảnh báo cho người sửa sau:** hai lớp này dùng `z` ÂM, nên thẻ cha PHẢI có
 * `isolate` và TUYỆT ĐỐI không được có `overflow-x-hidden`. CSS quy định khi một
 * trục `overflow` là `hidden` còn trục kia `visible` thì trục `visible` bị tính
 * lại thành `auto` — thẻ thành vùng cuộn và Chromium sơn nền của nó ĐÈ LÊN con
 * z âm. Ảnh vẫn load, vẫn `opacity:1`, đúng kích thước, chỉ là không bao giờ
 * nhìn thấy và không có lỗi nào báo ra. Đã mất khá lâu để tìm ra ở phase-08.
 */
export function BoardBackdrop() {
  return (
    <>
      {/* mm:2940:13432 */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-x-0 top-0 -z-20 h-[35.6vw] max-h-[512px]"
      >
        <Image
          src="/board/kv-background.png"
          alt=""
          fill
          priority
          sizes="100vw"
          className="object-cover object-top"
        />
      </div>
      {/* mm:I2940:13432;1210:12612 `Cover` */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-x-0 top-0 -z-10 h-[35.6vw] max-h-[512px] bg-gradient-to-b from-transparent via-[#00101A]/60 to-[#00101A]"
      />
    </>
  );
}
