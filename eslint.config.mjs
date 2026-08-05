import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
    // Không phải code ứng dụng — lint chúng chỉ tạo nhiễu:
    ".claude/**", // hook/script/venv của bộ kit Takumi, không do dự án này sở hữu
    "plans/**", // tài liệu kế hoạch + evidence
    "supabase/**", // file sinh bởi Supabase CLI
    "lib/supabase/database.types.ts", // sinh bởi `npm run supabase:types`
  ]),
]);

export default eslintConfig;
