# Stage 1: Build the React Application
FROM node:20.18-alpine AS builder

WORKDIR /app

# Copy dependency configs
COPY package.json package-lock.json /app/

# Install dependencies using clean install
RUN npm ci

# Copy source code and build
COPY . /app/
RUN npm run build

# Stage 2: Serve static compiled assets via Nginx
FROM nginx:1.27.3-alpine AS runner

# Standard OCI Metadata Labels
LABEL org.opencontainers.image.title="CareerPulse Frontend" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.description="Cloud Native Job Market Intelligence SPA View Layer" \
      org.opencontainers.image.source="https://github.com/ShashankMk031/careerpulse"

# Copy Nginx server configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy build assets
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

# Healthcheck checking Nginx responsiveness
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
