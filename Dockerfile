ARG CLIENT_DIR_NAME=client

# Builder for react client app
FROM node:alpine as client-app-builder
ARG CLIENT_DIR_NAME

# For the installation of some npm dependencies (e.g. node-gyp) a python version is required.
RUN apk --no-cache add g++ gcc libgcc libstdc++ linux-headers make python

# copy package.json and install all client app build dependencies
COPY $CLIENT_DIR_NAME/package*.json ./
RUN npm ci --only=production

# copy source code and build the react app
# set GENERATE_SOURCEMAP=false to prevent out of memory execption when building on Raspberry Pi
COPY $CLIENT_DIR_NAME ./
RUN export GENERATE_SOURCEMAP=false \
	&& npm run build

# debian-based python base image
# We can't use an alpine image (e.g. python:3-alpine3.9) because the vlc version distributed over alpine apk misses some modules,
# i.e. can not read https streams. Error: 'main tls client error: TLS client plugin not available'
FROM python:3-slim-stretch
ARG CLIENT_DIR_NAME

LABEL maintainer="Fabian Christoffel <faberchri@gmail.com>" \
	repository="https://github.com/faberchri/yousonos"

# install vlc, build-essential and pipenv (python dependency manager)
# build-essential is required for subsequent greenlet build.
# On alpine we would also need 'vlc-dev' and 'build-base' (for greenlet build).
RUN apt-get update \
	&& apt-get install --assume-yes --no-install-recommends build-essential vlc \
	&& apt-get clean --assume-yes \
	&& apt-get autoremove --assume-yes \
	&& rm -rf /var/lib/apt/lists/* \
	&& pip install pipenv

WORKDIR /yousonos

# copy built client app from builder image
COPY --from=client-app-builder build $CLIENT_DIR_NAME/build/

# install python dependencies
COPY Pipfile* ./
RUN pipenv install --system --deploy

# copy python sources
# Multiple copy steps required to prevent copying of unnecessary files while maintaining folder structure
COPY *.py ./
COPY server ./server/
COPY player ./player/

ENTRYPOINT ["python", "youSonos.py"]
