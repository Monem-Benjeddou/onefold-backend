FROM node:18-alpine

# Install system dependencies
RUN apk add --no-cache \
    git \
    python3 \
    make \
    g++ \
    curl \
    bash \
    jq

WORKDIR /app


# Install all dependencies (production and dev)
RUN npm ci --silent

# Create directories for outputs and ensure permissions
RUN mkdir -p artifacts deployments cache coverage \
    && chmod -R 755 artifacts deployments cache coverage



# Set environment variables
ENV NODE_ENV=development
ENV HARDHAT_NETWORK=hardhat
ENV PATH=/app/node_modules/.bin:$PATH

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD npm list hardhat > /dev/null 2>&1 || exit 1

# Default command (can be overridden)
CMD ["npx", "hardhat", "node", "--hostname", "0.0.0.0"] 