# FROM openjdk:11-jdk
FROM python:3.9

# Set environment variables
ARG RAG_HOME=/rag_app
ENV RAG_HOME=${RAG_HOME}

# ENV ACCEPT_EULA=Y
# ENV DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR ${RAG_HOME}

# Install required system dependencies, including Python
RUN apt-get update && \
    apt-get install -y \
    build-essential \
    libpoppler-cpp-dev \
    pkg-config \
    python3 \
    python3-dev \
    python3-pip \
    python3-venv \
    curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y unixodbc-dev 


RUN pip install --upgrade pip setuptools
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
