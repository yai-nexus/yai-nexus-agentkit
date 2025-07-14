import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  transpilePackages: ["@yai-nexus/fekit", "@yai-nexus/pino-support"],
  webpack: (config, { isServer }) => {
    if (!isServer) {
      // Provide fallbacks for Node.js modules when bundling for the browser
      config.resolve.fallback = {
        ...config.resolve.fallback,
        child_process: false,
        worker_threads: false,
        fs: false,
        "fs/promises": false,
        net: false,
        tls: false,
        crypto: false,
        stream: false,
        util: false,
        url: false,
        querystring: false,
        path: false,
        os: false,
        http: false,
        https: false,
        zlib: false,
        events: false,
        buffer: false,
      };
    }
    return config;
  },
};

export default nextConfig;
