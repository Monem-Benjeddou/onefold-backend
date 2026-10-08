# Onefold web app. The default (last) stage is the production image
# (Next.js standalone output); `target: dev` is used by docker compose.
FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# Development: dependencies baked in, source mounted by docker compose.
FROM deps AS dev
ENV NEXT_TELEMETRY_DISABLED=1
COPY . .
EXPOSE 3000
CMD ["npx", "next", "dev", "-H", "0.0.0.0", "-p", "3000"]

FROM node:22-alpine AS build
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:22-alpine
WORKDIR /app
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 PORT=3000 HOSTNAME=0.0.0.0
RUN addgroup -S onefold && adduser -S onefold -G onefold
COPY --from=build --chown=onefold:onefold /app/.next/standalone ./
COPY --from=build --chown=onefold:onefold /app/.next/static ./.next/static
COPY --from=build --chown=onefold:onefold /app/public ./public
USER onefold
EXPOSE 3000
CMD ["node", "server.js"]
