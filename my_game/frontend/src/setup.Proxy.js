const { createProxyMiddleware } = require("http-proxy-middleware");

module.exports = function (app) {
  app.use(
    "/start",
    createProxyMiddleware({
      target: "http://localhost:8000",
      changeOrigin: true,
    }),
  );
  app.use(
    "/guess",
    createProxyMiddleware({
      target: "http://localhost:8000",
      changeOrigin: true,
    }),
  );
  app.use(
    "/hint",
    createProxyMiddleware({
      target: "http://localhost:8000",
      changeOrigin: true,
    }),
  );
};
