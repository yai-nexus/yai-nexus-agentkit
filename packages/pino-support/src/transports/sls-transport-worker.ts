/**
 * SLS transport worker for pino
 * 
 * This is the actual worker that handles SLS logging in a separate process/thread
 * when used with pino.transport().
 */

import build from 'pino-abstract-transport';
import { SlsTransport } from '../sls/transport';
import { SlsTransportOptions } from '../sls/types';

export default async function (options: SlsTransportOptions) {
  const slsTransport = new SlsTransport(options);
  await slsTransport.start();
  
  return build(async function (source) {
    for await (const obj of source) {
      // Send each log message to SLS
      slsTransport.write(obj);
    }
  }, {
    async close() {
      await slsTransport.stop();
    }
  });
}