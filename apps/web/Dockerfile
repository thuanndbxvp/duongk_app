# Multi-stage build for Next.js (apps/web)

# ─── Stage 1: deps ───
FROM node:20-alpine AS deps
WORKDIR /app

# Copy root workspace manifests nếu dùng monorepo
COPY package.json package-lock.json* ./
# Nếu web có package.json riêng trong apps/web, copy cả 2
COPY apps/web/package.json ./apps/web/
RUN cd apps/web && npm ci

# ─── Stage 2: builder ───
FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY --from=deps /app/apps/web/node_modules ./apps/web/node_modules
COPY apps/web ./apps/web
WORKDIR /app/apps/web

ENV NEXT_TELEMETRY_DISABLED 1
RUN npm run build

# ─── Stage 3: runner (production) ───
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

RUN addgroup --system --gid 1001 nodejs \
    && adduser --system --uid 1001 nextjs

COPY --from=builder /app/apps/web/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/apps/web/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/apps/web/.next/static ./.next/static

USER nextjs
EXPOSE 3000
ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

CMD ["node", "server.js"]
