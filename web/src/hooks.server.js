import { BACKEND_URL } from '$lib/server/backend.js';
import { redirect } from '@sveltejs/kit';
import { LOCALES, LOCALE_COOKIE, resolveLocale } from '$lib/i18n.js';

// Hop-by-hop and encoding headers must not be copied across the proxy.
// Node's fetch has already decompressed the body, so a stale
// content-encoding would make the browser try to decompress it again.
const DROP_REQUEST = ['host', 'connection', 'content-length'];
const DROP_RESPONSE = ['content-encoding', 'content-length', 'transfer-encoding', 'connection'];

/**
 * Forward /api and /uploads to the backend. The browser only ever talks to
 * this origin, so there is no CORS, and the backend can stay on a private
 * network. Bodies stream both ways, which is what keeps SSE working; when
 * the backend closes a stream the browser sees it close too.
 */
async function proxy(event) {
  const { request, url } = event;
  const headers = new Headers(request.headers);
  for (const name of DROP_REQUEST) headers.delete(name);
  headers.set('x-forwarded-for', event.getClientAddress());

  const hasBody = !['GET', 'HEAD'].includes(request.method);
  let upstream;
  try {
    upstream = await fetch(`${BACKEND_URL}${url.pathname}${url.search}`, {
      method: request.method,
      headers,
      body: hasBody ? request.body : undefined,
      duplex: hasBody ? 'half' : undefined,
      signal: request.signal,
      redirect: 'manual',
    });
  } catch {
    return new Response(JSON.stringify({ detail: 'Backend unavailable.' }), {
      status: 502,
      headers: { 'content-type': 'application/json' },
    });
  }
  const responseHeaders = new Headers(upstream.headers);
  for (const name of DROP_RESPONSE) responseHeaders.delete(name);
  return new Response(upstream.body, { status: upstream.status, headers: responseHeaders });
}

export async function handle({ event, resolve }) {
  const path = event.url.pathname;
  if (path.startsWith('/api/') || path.startsWith('/uploads/')) {
    return proxy(event);
  }

  // ?lang=ru from the language links when JavaScript hasn't loaded yet:
  // remember it and redirect to the clean URL.
  const requested = event.url.searchParams.get('lang');
  if (requested && LOCALES.includes(requested)) {
    event.cookies.set(LOCALE_COOKIE, requested, {
      path: '/',
      maxAge: 60 * 60 * 24 * 365,
      sameSite: 'lax',
      httpOnly: false,
      secure: event.url.protocol === 'https:',
    });
    const clean = new URL(event.url);
    clean.searchParams.delete('lang');
    redirect(303, `${clean.pathname}${clean.search}`);
  }

  const locale = resolveLocale(event.cookies.get(LOCALE_COOKIE));
  event.locals.locale = locale;
  return resolve(event, {
    transformPageChunk: ({ html }) => html.replace('%lang%', locale),
  });
}
