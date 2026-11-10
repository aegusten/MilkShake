// Production entry: the SvelteKit handler behind gzip. adapter-node does not
// compress HTML or API responses itself; on a 3G phone the uncompressed menu
// page cost several extra round trips before first paint.
import http from 'node:http';
import compression from 'compression';
import { handler } from './build/handler.js';

const gzip = compression({
  // Never compress event streams: compression buffers output, which would
  // hold live updates back until the buffer fills.
  filter: (req, res) =>
    !String(res.getHeader('content-type') ?? '').startsWith('text/event-stream') &&
    compression.filter(req, res),
});

const port = Number(process.env.PORT ?? 3000);
http
  .createServer((req, res) => gzip(req, res, () => handler(req, res)))
  .listen(port, () => console.log(`Listening on http://0.0.0.0:${port}`));
