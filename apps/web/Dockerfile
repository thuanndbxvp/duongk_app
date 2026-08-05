# Multi-stage build for Next.js (apps/web)

# ─── Stage 1: builder ───
FROM node:20-alpine AS builder
WORKDIR /app

# Copy root + web package.json
COPY package.json package-lock.json* ./
COPY apps/web/package.json ./apps/web/

# Install deps trực tiếp trong apps/web
WORKDIR /app/apps/web
RUN npm install --no-audit --no-fund

# Copy toàn bộ source web
COPY apps/web ./

ENV NEXT_TELEMETRY_DISABLED 1
RUN npm run build

# ─── Stage 2: runner (production) ───
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

RUN addgroup --system --gid 1001 nodejs \
    && adduser --system --uid 1001 nextjs

COPY --from=builder --chown=nextjs:nodejs /app/apps/web/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/apps/web/.next/static ./.next/static
COPY --from=builder --chown=nextjs:nodejs /app/apps/web/public ./public

USER nextjs
EXPOSE 3000
ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

CMD ["node", "server.js"]
