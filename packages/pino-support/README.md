# @yai-nexus/pino-support

Production-ready cloud logging extensions for pino logger.

## Features

- 🚀 **High Performance**: Async batch processing with configurable buffer sizes
- 🔄 **Reliable**: Automatic retry with exponential backoff
- 📊 **Observable**: Built-in metrics, health checks, and monitoring
- 🛠 **TypeScript**: Full type safety with comprehensive type definitions
- 🌩️ **Multi-Cloud**: Support for Alibaba Cloud SLS, with extensible architecture
- 🔧 **Framework Agnostic**: Works with Next.js, Express, Fastify, and more

## Quick Start

```bash
npm install @yai-nexus/pino-support
```

### Basic Usage with SLS

```typescript
import pino from 'pino';
import { createSlsTransport } from '@yai-nexus/pino-support/sls';

const transport = createSlsTransport({
  endpoint: 'cn-hangzhou.log.aliyuncs.com',
  accessKeyId: process.env.SLS_AK_ID!,
  accessKeySecret: process.env.SLS_AK_KEY!,
  project: 'my-project',
  logstore: 'my-logstore',
  
  // Optional: Performance tuning
  batchSize: 100,
  flushInterval: 5000,
  maxRetries: 3
});

const logger = pino(transport);

logger.info('Hello SLS!', { userId: '123', action: 'login' });
```

### Advanced Configuration

```typescript
import { setupMonitoring } from '@yai-nexus/pino-support/monitoring';
import { setupGracefulShutdown } from '@yai-nexus/pino-support/utils';

// Setup monitoring
const monitor = setupMonitoring({
  transports: { sls: transport },
  alertThresholds: {
    errorRate: 0.1,  // Alert if error rate > 10%
    queueSize: 1000  // Alert if queue > 1000 items
  }
});

// Setup graceful shutdown
setupGracefulShutdown([transport], {
  timeout: 30000,  // 30 seconds timeout
  signals: ['SIGINT', 'SIGTERM']
});
```

## Architecture

This package follows the same modular architecture as `yai-loguru-support`:

- **Base Classes**: Abstract transport interface for extensibility
- **SLS Transport**: Production-ready Alibaba Cloud SLS integration
- **Monitoring**: Real-time metrics and alerting
- **Utils**: Graceful shutdown and lifecycle management

## Documentation

- [SLS Transport Guide](./docs/sls.md)
- [Monitoring Setup](./docs/monitoring.md)
- [Framework Integration](./docs/frameworks.md)
- [Migration Guide](./docs/migration.md)

## License

MIT