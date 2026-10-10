/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  distDir: process.env.NODE_ENV === "development" ? ".next-dev" : ".next",
  async rewrites() {
    const backend = (
      process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"
    ).replace(/\/$/, "");
    return [
      { source: "/backend-api/:path*", destination: `${backend}/:path*` },
    ];
  },
};

export default nextConfig;
