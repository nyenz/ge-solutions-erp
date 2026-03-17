# PATH: erp-frontend/Dockerfile

# STAGE 1: THE BUILDER
FROM node:18-slim AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# STAGE 2: THE SERVER
FROM nginx:alpine
# Copy the compressed 'dist' folder from Stage 1
COPY --from=build /app/dist /usr/share/nginx/html
# Copy our custom traffic guard config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]