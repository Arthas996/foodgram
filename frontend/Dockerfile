# build env
FROM node:21.7.1-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install --legacy-peer-deps
COPY . ./
ENV CI=false
RUN npm run build


FROM alpine:latest
WORKDIR /static
COPY --from=build /app/build/. /static/
RUN mv /static/static/* /static/ && rm -rf /static/static