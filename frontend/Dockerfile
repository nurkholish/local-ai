FROM node:20-alpine AS builder
WORKDIR /app

ARG VITE_API_URL=
ARG VITE_PROMETHEUS_URL=
ARG VITE_API_KEY=

ENV VITE_API_URL=${VITE_API_URL}
ENV VITE_PROMETHEUS_URL=${VITE_PROMETHEUS_URL}
ENV VITE_API_KEY=${VITE_API_KEY}

COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:1.27-alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=3s CMD wget -qO- http://127.0.0.1/ > /dev/null || exit 1
CMD ["nginx", "-g", "daemon off;"]