# debian-based python base image
# We can't use an alpine image (e.g. python:3-alpine3.9) because the vlc version distributed over alpine apk misses some modules,
# i.e. can not read https streams. Error: 'main tls client error: TLS client plugin not available'
FROM python:3-slim-stretch

LABEL maintainer="Fabian Christoffel <faberchri@gmail.com>" \
    repository="https://github.com/faberchri/yousonos"

ENV PROJECT_DIR=/yousonos \
	CLIENT_DIR_NAME=client

# install vlc and package managers, build-essential is required for greenlet build,
# on alpine we would also need 'vlc-dev' and 'build-base' for greenlet build.
RUN apt-get update \
	&& apt-get install --assume-yes --no-install-recommends build-essential vlc curl \
	&& curl -sL https://deb.nodesource.com/setup_12.x | bash - \
	&& apt-get install --assume-yes --no-install-recommends nodejs \
	&& apt-get remove --assume-yes curl \
	&& apt-get clean --assume-yes \
	&& apt-get autoremove --assume-yes \
	&& rm -rf /var/lib/apt/lists/* \
	&& pip install pipenv

WORKDIR $PROJECT_DIR

# install javascript and python dependencies
COPY $CLIENT_DIR_NAME/package*.json Pipfile* ./
RUN mkdir $CLIENT_DIR_NAME \
	&& mv package* $CLIENT_DIR_NAME/. \
	&& cd $CLIENT_DIR_NAME \
	&& npm ci --only=production \
	&& cd .. \
	&& pipenv install --system --deploy
	
# copy app
COPY . ./

# build the react app
RUN cd $CLIENT_DIR_NAME \
	&& npm run build

ENTRYPOINT ["python", "youSonos.py"]

