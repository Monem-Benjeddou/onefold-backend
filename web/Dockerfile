# Production image for the Onefold web app (Next.js standalone output).
FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

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
