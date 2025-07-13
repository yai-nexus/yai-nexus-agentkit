import { defineConfig } from 'tsup'

export default defineConfig({
  entry: ['src/index.ts'],
  format: ['cjs', 'esm'],
  dts: true,
  sourcemap: true,
  clean: true,
  splitting: false,
  treeshake: true,
  minify: false,
  external: ['pino', 'pino-pretty', 'pino/file'],
  esbuildOptions: (options) => {
    options.conditions = ['module']
  }
})