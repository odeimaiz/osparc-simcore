# NOTE: This is a first step towards a devcontainer
#       to perform operations like pip-compile or auto-formatting
#       that preserves identical environment across developer machines
#
# Python version can be upgraded if:
#   - Has been patched several times (avoid using the very first release for production)
#   - Can be installed with pyenv (SEE pyenv install --list )
#
#
ARG PYTHON_VERSION="3.8.10"
FROM python:${PYTHON_VERSION}-slim-buster as base


RUN apt-get update \
  && apt-get -y install --no-install-recommends\
  make \
  git \
  gawk \
  && rm -rf /var/lib/apt/lists/* \
  && apt-get clean


RUN pip --no-cache-dir install --upgrade \
  pip~=21.0.1  \
  wheel \
  setuptools


# devenv
RUN pip install \
  black \
  isort \
  pip-tools \
  bump2version \
  rope
