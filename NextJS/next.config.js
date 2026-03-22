/** @type {import('next').NextConfig} */

const nextConfig = {
  reactStrictMode: true,

  // Empty turbopack config silences the "webpack config but no turbopack config"
  // warning introduced in Next.js 16 where Turbopack is the default bundler.
  turbopack: {},
};

module.exports = nextConfig;
