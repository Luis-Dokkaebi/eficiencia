FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
# build-essential & cmake for dlib
# libgl1 & libglib2.0-0 for opencv
# libpq-dev for psycopg2
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libgl1 \
    libglib2.0-0 \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Default command
CMD ["python", "src/main.py"]
