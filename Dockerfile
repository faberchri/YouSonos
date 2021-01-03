ARG CLIENT_DIR_NAME=client

# Builder for react client app
#
# The output of this first build step are static (html/js/css) resources for the client app.
# I assume that these static resources can be identical on all target platforms.
# Hence, there is no need to run client-app-builder multiple times for each target platform.
#
# With '--platform=$BUILDPLATFORM' we say that the target platform (of the created image) should be
# identical to the platform where the build runs (if the build runs on GitHub action that is 'linux/amd64',
# if the build runs on a Raspberry Pi it is, probably, 'linux/arm/v7').
# See: https://docs.docker.com/buildx/working-with-buildx/#build-multi-platform-images
# and https://docs.docker.com/engine/reference/builder/#from
# and https://docs.docker.com/engine/reference/builder/#automatic-platform-args-in-the-global-scope
#
# As an alternative to setting '--platform=$BUILDPLATFORM' we could maybe also have two build steps in 
# .github/workflows/docker-image.yml. The first step would be platform agnostic (platforms: XXX not set) and 
# builds only the client-app-builder, i.e. stops after building client-app-builder (target: client-app-builder).
# The second step builds and pushes the target platform specific python image similar to the already existing
# build step in .github/workflows/docker-image.yml. In addition to 'platforms: XXX' we would also need to 
# set 'target: new-name-of-python-yousonos-image'.
# In a quick test of this approach, I run into the problem that in the second build step the output of the 
# first build step was used for only one platform (linux/amd64).
# See: https://docs.docker.com/develop/develop-images/multistage-build/#stop-at-a-specific-build-stage
# and https://github.com/marketplace/actions/build-and-push-docker-images#customizing
FROM --platform=$BUILDPLATFORM node:alpine as client-app-builder
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
# 
# We can't use an alpine image (e.g. python:3-alpine3.9) because the vlc version distributed over alpine apk misses some modules,
# i.e. can not read https streams. Error: 'main tls client error: TLS client plugin not available'
#
# This build step is specific for the target platform and, hence, must run once for each target platform.
# See also .github/workflows/docker-image.yml:Build the Docker image and push to DockerHub
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
