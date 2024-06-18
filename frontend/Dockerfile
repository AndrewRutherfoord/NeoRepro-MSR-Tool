FROM node:lts

WORKDIR /app/frontend

COPY ./frontend/package.json ./frontend/yarn.lock ./
RUN yarn install

COPY ./frontend .

CMD ["yarn", "run", "dev"]