# Stage 1: Build the React + Vite frontend
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependency definitions and install cleanly
COPY package*.json ./
RUN npm ci

# Copy application source and build assets
COPY . .
RUN npm run build

# Stage 2: Serve via Nginx
FROM nginx:alpine

# Copy compiled SPA assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom Nginx configuration with SPA routing and API proxy
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
