import QRCode from 'qrcode';
import { env } from '$env/dynamic/public';

/** The QR is drawn on the server as SVG: crisp at any print size, and the
 *  kiosk showing it needs no JavaScript. PUBLIC_MENU_URL wins when set,
 *  since behind a proxy the request origin may be an internal address. */
export async function load({ url }) {
  const target = env.PUBLIC_MENU_URL || `${url.origin}/`;
  const svg = await QRCode.toString(target, { type: 'svg', margin: 1, color: { dark: '#0c0c0d', light: '#ffffff' } });
  const isLocal = ['localhost', '127.0.0.1'].includes(url.hostname) && !env.PUBLIC_MENU_URL;
  return { target, svg, isLocal };
}
