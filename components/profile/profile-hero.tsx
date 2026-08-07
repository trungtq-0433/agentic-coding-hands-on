"use client";

import Image from "next/image";

import { montserrat } from "@/components/ui/fonts";
import { UserIcon } from "@/components/ui/icons";
import { useProfileT } from "./use-profile-text";
import type { ProfileSummary } from "./profile-types";

export interface ProfileHeroProps {
  profile: ProfileSummary;
}

/**
 * Khối hero (`mms_A_Info`, node `362:5052`) — avatar 200×200 (viền trắng 4px, bo
 * tròn — toạ độ đo THẬT qua MCP: x620-820 y184-384) + tên + phòng ban + hoa-thị.
 *
 * **Ảnh nền keyvisual KHÔNG lấy được**: node `image 20` (`I1210:12622;2167:5141`)
 * có ảnh fill trong Figma nhưng `get_media_files` trả về placeholder literal
 * `url(<path-to-image>)` — không phải URL thật, vì node không mang tiền tố
 * `MM_MEDIA_` (cùng cái bẫy đã gặp ở phase-07/09). Overlay gradient THẬT thì đo
 * được (`linear-gradient(8deg, #00101A 8.6%, rgba(0,19,32,0) 37.25%)`) — dùng
 * gradient đó trên nền đặc thay vì bịa ảnh, giữ đúng tông màu bản vẽ.
 *
 * **Hero tier bỏ khỏi MVP** (clarifications gap #7, "Điểm riêng của màn này") —
 * chỉ còn hoa-thị theo `starCount`. 0 sao thì ẩn cả dòng (TC_WEB_PROFILE_GUI_009:
 * "0 kudos khác với huy hiệu thấp nhất", không phải "hiện 0 sao").
 *
 * Avatar rỗng dùng lại đúng fallback `UserIcon` như `KudoCard`/`AccountMenu`
 * (nhất quán trạng thái "chưa có ảnh" trên toàn site).
 */
export function ProfileHero({ profile }: ProfileHeroProps) {
  const t = useProfileT();

  return (
    <div className="relative isolate flex w-full flex-col items-center">
      <div
        aria-hidden="true"
        className="h-[220px] w-full bg-[#00101A] sm:h-[280px]"
        style={{ backgroundImage: "linear-gradient(8deg, #00101A 8.6%, rgba(0,19,32,0) 37.25%)" }}
      />
      <div className="-mt-[100px] flex flex-col items-center gap-3 px-6 sm:-mt-[120px]">
        {profile.avatarUrl ? (
          <Image
            src={profile.avatarUrl}
            alt=""
            width={200}
            height={200}
            className="h-[200px] w-[200px] rounded-full border-4 border-white object-cover"
            priority
          />
        ) : (
          <span
            role="img"
            aria-label={t("hero.avatarPlaceholderAria")}
            className="flex h-[200px] w-[200px] items-center justify-center rounded-full border-4 border-white bg-[#00070C]"
          >
            <UserIcon className="h-20 w-20 text-[#FFEA9E]" />
          </span>
        )}
        <p className={`${montserrat.className} text-center text-2xl font-bold text-[#FFEA9E] sm:text-[32px]`}>
          {profile.fullName}
        </p>
        {profile.departmentName && (
          <p className={`${montserrat.className} text-center text-base font-bold text-white`}>
            {profile.departmentName}
          </p>
        )}
        {profile.starCount > 0 && (
          <span aria-label={t("hero.starsAria")} className="text-xl font-bold text-[#D4271D]">
            {"★".repeat(profile.starCount)}
          </span>
        )}
      </div>
    </div>
  );
}
