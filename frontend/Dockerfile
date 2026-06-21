# 多阶段构建 - 构建阶段
FROM node:18-alpine AS builder

WORKDIR /app

# 安装依赖（利用缓存层）
COPY package*.json ./
RUN npm ci --prefer-offline --no-audit --no-fund

# 构建应用
COPY . .
RUN npm run build

# 多阶段构建 - 运行阶段
FROM node:18-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production

# 只复制生产所需文件
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

# 安装生产依赖（standalone 模式不需要）
# RUN npm prune --production

EXPOSE 3000
ENV PORT=3000

# 使用 node 用户运行
USER node

CMD ["node", "server.js"]
