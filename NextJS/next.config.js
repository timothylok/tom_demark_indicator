/** @type {import('next').NextConfig} */

const nextConfig = {
  reactStrictMode: true,

  // plotly.js is a large CJS module; this tells webpack to treat it properly.
  webpack: (config) => {
    config.resolve.fallback = { fs: false };
    return config;
  },
};

module.exports = nextConfig;
