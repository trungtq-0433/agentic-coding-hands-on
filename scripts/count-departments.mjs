#!/usr/bin/env node
/**
 * Đếm phòng ban từ CSV spec MoMorph gốc — chống đếm bằng mắt.
 *
 * Nguồn ghi danh sách dưới dạng một chuỗi phẳng, ngăn cách bằng khoảng trắng,
 * tên phân cấp thì nối bằng " - " (vd "CEVC1 - DSV - UI/UX 1"). Khoảng trắng
 * vừa là dấu ngăn giữa các mục vừa nằm trong tên, nên không tách được bằng
 * split đơn thuần — phải bám vào tập mã gốc.
 *
 * Chạy: node scripts/count-departments.mjs
 */
import { readFileSync } from "node:fs";

const CSV =
  "plans/260805-1032-sun-kudos-website/research/momorph/csv/spec-dropdown-phong-ban-WXK5AYB_rG.csv";

/** Mã gốc — một mục mới luôn bắt đầu bằng một trong các mã này. */
const ROOT_CODES = [
  "CTO", "SPD", "FCOV", "CEVC1", "CEVC2", "CEVC3", "CEVC4",
  "CEVEC", "STVC", "OPDC", "GEU", "PAO", "IAV", "CPV", "BDV",
];

/** Rút đoạn "Danh sách phòng ban: …" ra khỏi CSV. */
function extractRawList(csvText) {
  const marker = "Danh sách phòng ban:";
  const start = csvText.indexOf(marker);
  if (start === -1) throw new Error(`Không tìm thấy "${marker}" trong ${CSV}`);
  const rest = csvText.slice(start + marker.length);
  // Đoạn kết thúc ở dấu ngoặc kép đóng ô CSV.
  return rest.slice(0, rest.indexOf('"')).trim();
}

/**
 * Tách chuỗi phẳng thành từng mục.
 * Một token mở mục mới khi nó là mã gốc VÀ token trước đó không phải "-"
 * (nếu là "-" thì nó đang là thành phần con của tên đang dựng dở).
 */
function splitEntries(raw) {
  const tokens = raw.split(/\s+/).filter(Boolean);
  const entries = [];
  let current = [];

  for (let i = 0; i < tokens.length; i++) {
    const token = tokens[i];
    const isRoot = ROOT_CODES.includes(token);
    const prevIsDash = i > 0 && tokens[i - 1] === "-";

    if (isRoot && !prevIsDash && current.length > 0) {
      entries.push(current.join(" "));
      current = [];
    }
    current.push(token);
  }
  if (current.length > 0) entries.push(current.join(" "));
  return entries;
}

/** `CEVC1 - DSV - UI/UX 1` → code `CEVC1-DSV-UI-UX-1`, parent `CEVC1 - DSV`. */
function toRow(name) {
  const parts = name.split(" - ").map((s) => s.trim());
  const code = parts
    .join("-")
    .replace(/[^A-Za-z0-9-]+/g, "-")
    .replace(/-+/g, "-")
    .replace(/^-|-$/g, "")
    .toUpperCase();
  const parent = parts.length > 1 ? parts.slice(0, -1).join(" - ") : null;
  return { name, code, parent };
}

const entries = splitEntries(extractRawList(readFileSync(CSV, "utf8")));
const rows = entries.map(toRow);

const seenNames = new Set();
const duplicates = rows.filter((r) => {
  if (seenNames.has(r.name)) return true;
  seenNames.add(r.name);
  return false;
});

rows.forEach((r, i) => {
  const flag = r.name.split(" - ").every((p, _, a) => a.length > 1 && p === a[0])
    ? "  ← trùng tên cha"
    : "";
  console.log(
    `${String(i + 1).padStart(2)}. ${r.code.padEnd(22)} ${r.name}${flag}`,
  );
});

console.log(`\ntổng: ${rows.length} mục`);
console.log(`trùng lặp: ${duplicates.length ? duplicates.map((d) => d.name).join(", ") : "không có"}`);
