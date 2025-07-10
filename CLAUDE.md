# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Structure

This is a monorepo containing:
- `packages/yai-nexus-fekit/` - Main SDK package for Next.js integration with yai-nexus-agentkit and CopilotKit
- `examples/nextjs-app/` - Next.js 15 example application with React 19 and TailwindCSS
- `examples/python-backend/` - Python backend example (currently empty)

## Development Commands

### Main SDK Package (`packages/yai-nexus-fekit/`)
```bash
cd packages/yai-nexus-fekit
npm run build    # Build the SDK using tsup
npm run dev      # Build in watch mode
```

### Next.js Example App (`examples/nextjs-app/`)
```bash
cd examples/nextjs-app
npm run dev      # Start development server with Turbopack
npm run build    # Build for production
npm run start    # Start production server
npm run lint     # Run ESLint
```

## Architecture

### SDK Package (`@yai-nexus/fekit`)
- Built with TypeScript and bundled using tsup
- Configured as both CommonJS and ESM modules with TypeScript declarations
- Currently re-exports from `@ag-ui/proto` package
- Includes "use client" banner for Next.js client-side compatibility
- Peer dependencies: CopilotKit, Next.js 14+, React 18+

### Build Configuration
- Uses shared TypeScript configuration via `tsconfig.base.json`
- tsup configured for dual format output (CJS/ESM) with sourcemaps
- TypeScript targeting ES2020 with strict mode enabled

### Dependencies
The SDK depends on the ag-ui ecosystem:
- `@ag-ui/client`, `@ag-ui/core`, `@ag-ui/encoder`, `@ag-ui/proto` (v0.0.31)

## Key Files
- `packages/yai-nexus-fekit/src/index.ts` - Main entry point, re-exports from @ag-ui/proto
- `packages/yai-nexus-fekit/src/handler.ts` - Currently empty, likely for future CopilotKit integration
- `tsconfig.base.json` - Shared TypeScript configuration
- `tsup.config.ts` - Build configuration for the SDK

## Development Notes
- The project is in early development stage with many placeholder files
- SDK is designed to integrate yai-nexus-agentkit with CopilotKit in Next.js applications
- Example application uses latest Next.js 15 with React 19 and TailwindCSS 4