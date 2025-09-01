FROM mcr.microsoft.com/devcontainers/python:1-3.11-bookworm

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    # Set the UID/GID to match host user
    USER_UID=1000 \
    USER_GID=100

# Create a non-root user with the same UID/GID as the host user if it doesn't exist
RUN if ! getent group $USER_GID >/dev/null; then groupadd --gid $USER_GID vscode; fi && \
    if ! getent passwd $USER_UID >/dev/null; then useradd --uid $USER_UID --gid $USER_GID -m vscode; fi && \
    # Add sudo support for the non-root user
    apt-get update && \
    apt-get install -y sudo && \
    echo 'vscode ALL=(root) NOPASSWD:ALL' > /etc/sudoers.d/vscode && \
    chmod 0440 /etc/sudoers.d/vscode && \
    # Clean up
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY --chown=${USER_UID}:${USER_GID} requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Switch to the non-root user
USER vscode
