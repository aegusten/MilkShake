import adapter from '@sveltejs/adapter-node';

/** @type {import('@sveltejs/kit').Config} */
export default {
  kit: {
    // Static assets are written as .gz and .br next to the originals.
    adapter: adapter({ precompress: true }),
    // The whole stylesheet is a few KB, so ship it inside the HTML rather
    // than as a second blocking request.
    inlineStyleThreshold: 32768,
  },
};
