import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "export",
  basePath: "/ai-company-directory",
  images: {
    unoptimized: true,
  },
  reactCompiler: true,
};

export default nextConfig;
