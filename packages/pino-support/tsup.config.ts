import { defineConfig } from 'tsup'

export default defineConfig({
  entry: {
    index: 'src/index.ts',
    'sls/index': 'src/sls/index.ts',
    'monitoring/index': 'src/monitoring/index.ts',
    'utils/index': 'src/utils/index.ts'
  },
  format: ['cjs', 'esm'],
  dts: true,
  sourcemap: true,
  clean: true,
  splitting: false,
  treeshake: true,
  minify: false,
  external: ['pino', '@alicloud/sls'],
  esbuildOptions: (options) => {
    options.conditions = ['module']
  }
})