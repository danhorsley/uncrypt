
const { createProxyMiddleware } = require("http-proxy-middleware");

module.exports = function (app) {
  app.use(
    ["/start", "/guess", "/hint", "/get_attribution", "/save_quote"],
    createProxyMiddleware({
      target: "http://0.0.0.0:8000",
      changeOrigin: true,
      cookieDomainRewrite: {
        "*": ""
      },
      withCredentials: true,
      secure: false,
      xfwd: true,
      logLevel: 'debug',
      onError: (err, req, res) => {
        console.error('Proxy error:', err);
        res.writeHead(500, {
          'Content-Type': 'text/plain',
        });
        res.end('Proxy error: ' + err.message);
      },
      headers: {
        Connection: 'keep-alive'
      },
      onProxyRes: function(proxyRes, req, res) {
        // Log the response headers for debugging
        console.log('ProxyRes headers:', proxyRes.headers);
        console.log('ProxyRes status:', proxyRes.statusCode);

        // Ensure cookies are properly passed
        if (proxyRes.headers['set-cookie']) {
          const cookies = proxyRes.headers['set-cookie'].map(cookie => 
            cookie.replace(/Domain=[^;]+;/i, '')
                 .replace(/SameSite=[^;]+;/i, 'SameSite=None;')
                 .replace(/Secure/i, 'Secure')
          );
          proxyRes.headers['set-cookie'] = cookies;
        }
      }
    }),
  );
};
