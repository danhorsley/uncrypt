
const { createProxyMiddleware } = require("http-proxy-middleware");

module.exports = function (app) {
  app.use(
    ["/start", "/guess", "/hint", "/get_attribution", "/save_quote"],
    createProxyMiddleware({
      target: "http://0.0.0.0:8000",
      changeOrigin: true,
      methods: ["GET", "POST", "PUT", "DELETE"],
      cookieDomainRewrite: "0.0.0.0",
      withCredentials: true
    }),
  );
};
