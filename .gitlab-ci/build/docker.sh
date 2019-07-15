#!/bin/sh

set -e

if [ "$1" = "setup" ]
then
  set -x
  docker login -u gitlab-ci-token -p $CI_JOB_TOKEN $CI_REGISTRY
  apk add git
else
  set -x

  # Patch the version on the fly
  VERSION=$(git describe)
  sed -i "s#^__version__ = .*\$##" reactobus/__about__.py
  echo "__version__ = $VERSION" >> reactobus/__about__.py

  # Build the docker image
  docker build -t $CI_REGISTRY_IMAGE:latest .

  # Push only for tags or master
  if [ "$CI_COMMIT_REF_SLUG" = "master" -o -n "$CI_COMMIT_TAG" ]
  then
    docker push $CI_REGISTRY_IMAGE:latest
  fi
fi
