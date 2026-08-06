"use client";

import Image from "next/image";

import { ChevronRightIcon, GridIcon, UserIcon } from "./icons";
import { montserrat } from "./fonts";
import { useCommonUiT } from "./use-common-ui-text";
import { useDropdown } from "./use-dropdown";

export interface AccountMenuProfile {
  name: string;
  avatarUrl?: string | null;
}

export interface AccountMenuProps {
  profile: AccountMenuProfile;
  isAdmin: boolean;
  onProfile: () => void;
  onAdmin?: () => void;
  onSignOut: () => void;
}

/**
 * Menu tài khoản — gộp 2 màn Figma "Dropdown profile" (z4sCl3_Qtk) và
 * "Dropdown profile Admin" (54rekaCHG1) thành 1 component, khác nhau bởi
 * prop `isAdmin` (chốt trong phase-06.md, không tách riêng).
 */
export function AccountMenu({ profile, isAdmin, onProfile, onAdmin, onSignOut }: AccountMenuProps) {
  const t = useCommonUiT();
  const { open, setOpen, rootRef } = useDropdown<HTMLDivElement>();

  return (
    <div ref={rootRef} className={`${montserrat.className} relative inline-block`}>
      <button
        type="button"
        onClick={() => setOpen((prev) => !prev)}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label={t("accountMenu.triggerAria")}
        className="flex items-center gap-2 rounded-full border border-[#998C5F] bg-[#00070C] px-2 py-1"
      >
        {profile.avatarUrl ? (
          <Image
            src={profile.avatarUrl}
            alt=""
            width={32}
            height={32}
            className="h-8 w-8 rounded-full object-cover"
          />
        ) : (
          <UserIcon className="h-8 w-8 text-[#FFEA9E]" />
        )}
        <span className="text-base font-bold text-white">{profile.name}</span>
      </button>
      {open && (
        <ul
          role="menu"
          className="absolute right-0 z-20 mt-1 min-w-[200px] rounded-lg border border-[#998C5F] bg-[#00070C] p-1.5"
        >
          <li role="none">
            <button
              type="button"
              role="menuitem"
              onClick={() => {
                onProfile();
                setOpen(false);
              }}
              style={{ textShadow: "0 4px 4px rgba(0,0,0,.25), 0 0 6px #FAE287" }}
              className="flex w-full items-center gap-2 rounded bg-[#FFEA9E]/10 px-4 py-4 text-left text-base font-bold leading-6 tracking-[0.15px] text-white"
            >
              <UserIcon className="h-6 w-6" />
              <span>{t("accountMenu.profile")}</span>
            </button>
          </li>
          {isAdmin && (
            <li role="none">
              <button
                type="button"
                role="menuitem"
                onClick={() => {
                  onAdmin?.();
                  setOpen(false);
                }}
                className="flex w-full items-center gap-2 rounded px-4 py-4 text-left text-base font-bold leading-6 tracking-[0.15px] text-white hover:bg-[#FFEA9E]/10"
              >
                <GridIcon className="h-6 w-6" />
                <span>{t("accountMenu.dashboard")}</span>
              </button>
            </li>
          )}
          <li role="none">
            <button
              type="button"
              role="menuitem"
              onClick={() => {
                onSignOut();
                setOpen(false);
              }}
              className="flex w-full items-center gap-2 rounded px-4 py-4 text-left text-base font-bold leading-6 tracking-[0.15px] text-white hover:bg-[#FFEA9E]/10"
            >
              <ChevronRightIcon className="h-6 w-6" />
              <span>{t("accountMenu.logout")}</span>
            </button>
          </li>
        </ul>
      )}
    </div>
  );
}
