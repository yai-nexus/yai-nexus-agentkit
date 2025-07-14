const { createLogger } = require('./packages/pino-support/dist/index.js');
const fs = require('fs');

// Clean up any existing test file
const testFile = './test-pretty.log';
if (fs.existsSync(testFile)) {
  fs.unlinkSync(testFile);
}

console.log('Testing pretty file logging...');

const logger = createLogger({
  serviceName: 'test-service',
  level: 'debug',
  console: { enabled: true, pretty: true },
  file: { enabled: true, path: testFile, pretty: true }
});

logger.info('Test message 1');
logger.warn('Test warning');
logger.error('Test error', { foo: 'bar', timestamp: new Date().toISOString() });

// Wait a bit for file writing
setTimeout(() => {
  if (fs.existsSync(testFile)) {
    console.log('\n=== File Content ===');
    console.log(fs.readFileSync(testFile, 'utf8'));
  } else {
    console.log('No log file created');
  }
}, 500);
EOF < /dev/null