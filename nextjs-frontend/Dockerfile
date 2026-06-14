FROM node:20-bookworm

WORKDIR /app

RUN npm install -g pnpm

COPY pnpm-lock.yaml package.json ./
RUN pnpm install --frozen-lockfile

COPY . .
RUN pnpm build --webpack

EXPOSE 3000
CMD node_modules/.bin/next start -p ${PORT:-3000}
