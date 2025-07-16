import { defineConfig } from 'tsup';

export default defineConfig({
  entry: ['src/index.ts'],
  format: ['cjs', 'esm'],
  dts: true,
  clean: true,
  sourcemap: true,
  minify: false,
  target: 'node16',
  external: [
    'loglayer',
    '@loglayer/transport-pino',
    '@loglayer/transport-winston', 
    '@loglayer/transport-simple-pretty-terminal',
    '@loglayer/plugin-redaction',
    'pino',
    'winston'
  ],
  banner: {
    js: '// @yai-nexus/loglayer-support - LogLayer 统一日志解决方案'
  }
});
