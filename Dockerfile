# Python base image
FROM python:3.11-slim
ENV PYTHONUNBUFFERED 1

# Set workdir
WORKDIR /code

# Install system deps (if any, e.g. for psycopg2)
RUN apt-get update && apt-get install -y build-essential libpq-dev


RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    python3-dev \
    libffi-dev \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    libjpeg-dev \
    libfreetype6-dev \
    pkg-config \
    curl \
    git \
 && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy project code
COPY . .
COPY manage.py .
COPY config/entrypoint.sh /code/config/entrypoint.sh

# Set environment variables (for Django settings)
ENV DJANGO_SETTINGS_MODULE=config.settings

# Make entrypoint executable
RUN chmod +x /code/config/entrypoint.sh

# Expose port 8000 (if needed)
EXPOSE 8000

# Entry point to run migrations and then start server
ENTRYPOINT ["/code/config/entrypoint.sh"]
