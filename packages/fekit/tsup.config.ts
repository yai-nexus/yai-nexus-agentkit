import { defineConfig } from "tsup";

export default defineConfig([
  {
    entry: {
      client: "src/client.ts",
    },
    format: ["cjs", "esm"],
    dts: true,
    sourcemap: true,
    clean: true,
    banner: {
      js: '"use client";',
    },
  },
  {
    entry: {
      server: "src/server.ts",
    },
    format: ["cjs", "esm"],
    dts: true,
    sourcemap: true,
  },
]); 