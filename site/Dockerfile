#-------------------------- build stage ---------------------
FROM node:19-alpine as build-stage
WORKDIR /app

#install dependencies
COPY ./frontend/package*.json ./
RUN npm ci --force

#main fe logic (docker optimization)
COPY ./frontend ./

#copy release config
COPY ./release/config.js ./src/common

RUN npm run build

#-------------------------- prod stage ----------------------
FROM tiangolo/uwsgi-nginx-flask:python3.8 as production-stage

#serve static/index.html
ENV STATIC_INDEX 1
ENV LISTEN_PORT 80

#install dependencies
COPY ./backend/requirements.txt /app
RUN pip install -r /app/requirements.txt

#copy assets
RUN mkdir /app/static/

#BE app (docker optimization)
COPY ./backend /app

#copy release config
# COPY ./release/config.py /app

COPY --from=build-stage /app/dist /app/static
