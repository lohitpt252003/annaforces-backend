# File: Dockerfile
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install language runtimes and compilers
RUN apt-get update && \
    apt-get install -y \
    build-essential \
    gcc \
    g++ \
    openjdk-17-jdk \
    python3 \
    python3-pip \
    && apt-get clean

# Set environment variable for Java
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

# Default working directory (can be overridden)
WORKDIR /judge

# Entrypoint is not set to judge.py since it will be mounted
CMD [ "bash" ]
