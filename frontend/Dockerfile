FROM node:22-alpine@sha256:0a7108bf6c7bf5de370ffb1a3ed6be93d405b43ff159f681a8d18c0e2bc2e402 AS builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY index.html tsconfig.json vite.config.ts ./
COPY src ./src
RUN npm run build

FROM nginx:1.27-alpine@sha256:65645c7bb6a0661892a8b03b89d0743208a18dd2f3f17a54ef4b76fb8e2f2a10 AS runtime
ENV BACKEND_UPSTREAM=backend:8000
COPY nginx.conf /etc/nginx/civicpulse.conf.template
COPY docker-entrypoint.sh /usr/local/bin/civicpulse-entrypoint
RUN sed -i 's/\r$//' /usr/local/bin/civicpulse-entrypoint \
    && chmod 755 /usr/local/bin/civicpulse-entrypoint \
    && rm -rf /usr/share/nginx/html/*
COPY --from=builder /app/dist/ /usr/share/nginx/html/
USER 101:101
EXPOSE 8080
STOPSIGNAL SIGQUIT
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=5 \
    CMD ["wget", "-q", "-O", "/dev/null", "http://127.0.0.1:8080/health"]
ENTRYPOINT ["/usr/local/bin/civicpulse-entrypoint"]
CMD ["nginx", "-c", "/tmp/civicpulse-nginx.conf", "-g", "daemon off;"]
