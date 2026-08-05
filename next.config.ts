import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    // `images.domains` đã deprecated ở Next 16 — dùng remotePatterns.
    // Thiếu khai báo này thì next/image throw với mọi host lạ, và lỗi CHỈ lộ ra
    // khi đăng nhập Google thật (seed demo không có avatar nên không bung).
    remotePatterns: [
      // Avatar Google trả về từ OAuth (raw_user_meta_data.avatar_url)
      { protocol: "https", hostname: "lh3.googleusercontent.com" },
      // Supabase Storage của stack local
      {
        protocol: "http",
        hostname: "127.0.0.1",
        port: "54321",
        pathname: "/storage/v1/object/public/**",
      },
    ],
  },
};

export default nextConfig;
