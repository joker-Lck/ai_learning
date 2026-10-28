# ── 构建阶段 ──
FROM node:20-alpine AS builder

WORKDIR /app

# npm 国内镜像加速
RUN npm config set registry https://registry.npmmirror.com

COPY package*.json ./
RUN npm install --prefer-offline --no-audit --no-fund

COPY . .
ENV NODE_ENV=production
RUN mkdir -p public && npm run build

# ── 运行阶段 ──
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV PORT=3000

COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

USER node

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD wget -qO- http://localhost:3000/ || exit 1

CMD ["node", "server.js"]
