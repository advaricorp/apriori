# Build stage
FROM node:18-alpine AS build

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies (using install instead of ci due to lock file sync issues)
RUN npm install --legacy-peer-deps

# Copy source code
COPY . .

# Build the React app
RUN npm run build

# Production stage
FROM nginx:alpine

# Remove default nginx configuration
RUN rm -f /etc/nginx/conf.d/default.conf

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built React app
COPY --from=build /app/build /usr/share/nginx/html

# Set proper permissions for nginx user
RUN chown -R nginx:nginx /usr/share/nginx/html

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"] 