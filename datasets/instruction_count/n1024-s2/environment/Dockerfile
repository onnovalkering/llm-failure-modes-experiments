FROM ubuntu:26.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      ca-certificates \
      curl \
      git \
      nodejs \
      npm \
      python-is-python3 \
      python3 \
      python3-pip \
      python3-venv \
      ripgrep \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
