FROM node:22-alpine AS build
WORKDIR /app
# No lockfile in git (see CLAUDE.md), so npm install, not npm ci.
COPY package.json .npmrc ./
RUN npm install
COPY . .
# Same origin: Caddy sends /api/* to the backend.
ENV VITE_API_BASE_URL=/api
RUN npm run build

FROM caddy:2-alpine
COPY Caddyfile /etc/caddy/Caddyfile
COPY --from=build /app/dist /srv
EXPOSE 3000
