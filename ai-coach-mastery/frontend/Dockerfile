# =============================================================================
# frontend — multi-stage: dev (ng serve), test (karma headless), prod (nginx)
# =============================================================================

# ---- Base deps ----------------------------------------------------------------
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json ./
# No lockfile committed yet in Step 1 — npm install resolves and creates one.
RUN npm install

# ---- Dev stage: Angular dev server with API proxy -----------------------------
FROM deps AS dev
COPY . .
EXPOSE 4200
CMD ["npm", "start", "--", "--poll", "2000"]

# ---- Test stage: headless Chrome unit tests -----------------------------------
FROM deps AS test
RUN apk add --no-cache chromium
ENV CHROME_BIN=/usr/bin/chromium-browser
COPY . .
CMD ["npm", "test"]

# ---- Build stage ---------------------------------------------------------------
FROM deps AS build
COPY . .
RUN npm run build

# ---- Prod stage: static assets behind nginx ------------------------------------
FROM nginx:1.27-alpine AS prod
COPY --from=build /app/dist/frontend/browser /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
