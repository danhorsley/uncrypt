
const { createProxyMiddleware } = require("http-proxy-middleware");

module.exports = function (app) {
  app.use(
    ["/start", "/guess", "/hint", "/get_attribution", "/save_quote"],
    createProxyMiddleware({
      target: "http://0.0.0.0:8000",
      changeOrigin: true,
      cookieDomainRewrite: '',
      withCredentials: true,
      headers: {
        Connection: 'keep-alive'
      },
      onProxyRes: function(proxyRes, req, res) {
        // Log the response headers for debugging
        console.log('ProxyRes headers:', proxyRes.headers);
        
        // Ensure cookies are properly passed
        if (proxyRes.headers['set-cookie']) {
          const cookies = proxyRes.headers['set-cookie'].map(cookie => 
            cookie.replace(/Domain=[^;]+;/i, '')
                 .replace(/SameSite=[^;]+;/i, 'SameSite=None;')
                 .replace(/Secure/i, '')
          );
          proxyRes.headers['set-cookie'] = cookies;
        }
      }
    }),
  );
};
const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  app.use(
    ['/start', '/guess', '/hint', '/get_attribution', '/save_quote'],
    createProxyMiddleware({
      target: 'http://localhost:8000',
      changeOrigin: true,
      secure: false,
      xfwd: true,
      withCredentials: true,
      headers: {
        Connection: 'keep-alive'
      }
    })
  );
};
