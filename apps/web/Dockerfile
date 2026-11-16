# Build stage
FROM node:20-alpine AS build

WORKDIR /app

COPY apps/web/package.json ./
RUN npm install

COPY apps/web/ ./
RUN npm run build

# Serve stage
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY infra/nginx-web.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
