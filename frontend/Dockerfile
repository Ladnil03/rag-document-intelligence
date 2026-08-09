# Multi-stage build for the React frontend.
#
# Stage 1: build the static bundle with Node + Vite. VITE_API_URL is
# the only environment the browser bundle ever sees; everything else
# stays in backend/.env.
#
# Stage 2: serve the bundle with nginx. We rewrite /api/* to the FastAPI
# service so the browser only sees a single origin in production — no
# CORS dance, no second port to remember.

# --- Build ---
FROM node:20-alpine AS build
WORKDIR /app

# Cache the install layer.
COPY package.json package-lock.json* ./
RUN npm ci --no-audit --no-fund || npm install --no-audit --no-fund

COPY . .
ARG VITE_API_URL=/api
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

# --- Serve ---
FROM nginx:alpine AS runtime
# Drop the default site and ship ours.
RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/app.conf

# Static assets.
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD wget -qO- http://localhost/ >/dev/null 2>&1 || exit 1

CMD ["nginx", "-g", "daemon off;"]
