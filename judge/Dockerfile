# File: Dockerfile
FROM ubuntu:22.04

# Prevents interactive prompts during package install
ENV DEBIAN_FRONTEND=noninteractive

# Install compilers/interpreters
RUN apt-get update && \
    apt-get install -y \
    build-essential \
    gcc \
    g++ \
    openjdk-17-jdk \
    python3 \
    python3-pip \
    && apt-get clean

# Set JAVA_HOME for Java compilation
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

# Create working directory
WORKDIR /judge

# Copy your judge script into the container
COPY judge.py /judge/judge.py

ENTRYPOINT ["python3", "judge.py"]
