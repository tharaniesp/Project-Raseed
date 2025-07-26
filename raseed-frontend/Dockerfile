# Stage 1: Build the React app
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package.json and install deps first (to cache better)
COPY package.json ./
COPY package-lock.json ./
RUN npm install

# Copy the rest of the source code and build
COPY . ./
RUN npm run build

# Stage 2: Serve the build using a lightweight server
FROM nginx:alpine

# Copy built assets to NGINX’s web root
COPY --from=builder /app/build /usr/share/nginx/html

# Replace default NGINX config with minimal SPA support
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
