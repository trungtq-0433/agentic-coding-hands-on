# Phase 06 — UI shared components

## MoMorph refs:
- Dropdown Hashtag filter: https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/JWpsISMAaM
- Dropdown Phòng ban: https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/WXK5AYB_rG
- Dropdown list hashtag: https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/p9zO-c4a4x
- Dropdown ngôn ngữ: https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/hUyaaugye2
- Dropdown profile: https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/z4sCl3_Qtk
- Dropdown profile Admin: https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/54rekaCHG1
- Addlink Box: https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/OyDLDuSGEa
- FAB 1: https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/_hphd32jN2
- FAB 2: https://momorph.ai/files/9ypp4enmFmdK3YAFJLIu6C/screens/Sv7DFwBw1h
- Clarifications: plans/260805-1032-sun-kudos-website/clarifications.md

**Track:** A · **P1** · pending · **4h** · chạy TRƯỚC phase 07–15 (chain nội bộ Track A). Không phụ thuộc Track B.
**File ownership:** `components/ui/**`, `components/layout/**`, `locales/*/common-ui.json`

## Mục tiêu & ngoài phạm vi
Dựng component dùng chung 9 màn trên + `SiteHeader`/`SiteFooter` + `CountdownTimer` qua `momorph-implement-design`; mock data từ chính Figma. Hashtag/phòng ban thật, đăng xuất, đổi ngôn ngữ, mở modal → prop/callback, phase-16 nối.
- `z4sCl3_Qtk` + `54rekaCHG1` là MỘT component 2 biến thể (prop `isAdmin`); FAB 1 + FAB 2 là 2 trạng thái của MỘT component.

## Integration contract
- `<FilterDropdown items value onChange placeholder />` · `<MultiHashtagPicker items value onChange max={5} />` (đủ 5 thì disable phần còn lại) · `<LanguageSwitcher locale onChange />`
- `<AccountMenu profile isAdmin onProfile onAdmin onSignOut />` · `<AddLinkDialog open onCancel onSave({text,url}) errors />` (lỗi nhận qua prop)
- `<KudosFab onRules onCompose />` · `<CountdownTimer targetIso tickMs labels />` (`tickMs`: 1000 hoặc 60000) · `<SiteHeader/>`, `<SiteFooter/>` (nav và slot đều là prop)
- **`<ModalShell open onClose labelledBy>{children}</ModalShell>`** — backdrop, Esc, focus trap, scroll-lock **đếm tham chiếu**. Phase-10/13/15 song song, mỗi phase tự dựng chrome sẽ ra 3 Esc-listener và 3 kiểu khoá scroll đá nhau → chrome về đây, 3 phase kia chỉ compose nội dung.

## Acceptance
- Mỗi component render độc lập với mock props; `grep -rn "lib/supabase\|lib/data\|lib/actions" components/` trả rỗng. Mọi chuỗi qua `locales/*/common-ui.json`, đủ `vi` lẫn `en`.
- `ModalShell`: mở A → mở B → đóng B → nền **vẫn khoá**; đóng A → nền mở lại. Esc đóng modal trên cùng. Tab không thoát ra ngoài modal.
