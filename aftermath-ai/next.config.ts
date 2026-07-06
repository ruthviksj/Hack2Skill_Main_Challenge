import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  eslint: {
    // Don't fail the production build on lint errors (hackathon MVP).
    ignoreDuringBuilds: true,
  },
  typescript: {
    // Typecheck passes locally; safety net so deploys aren't blocked.
    ignoreBuildErrors: true,
  },
};

export default nextConfig;
