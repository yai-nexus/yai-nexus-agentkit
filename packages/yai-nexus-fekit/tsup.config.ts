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
  },
  {
    entry: {
      server: "src/server.ts",
    },
    format: ["cjs", "esm"],
    dts: true,
    sourcemap: true,
    clean: false, // Do not clean for the second build
  },
]); 