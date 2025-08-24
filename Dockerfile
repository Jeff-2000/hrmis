# Python base image
FROM python:3.11-slim
ENV PYTHONUNBUFFERED 1

# Set workdir
WORKDIR /code

# Install system deps (if any, e.g. for psycopg2)
RUN apt-get update && apt-get install -y build-essential libpq-dev

# Copy requirements and install
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy project code
# COPY hrmis/ hrmis/
COPY hrmis/ config/
COPY manage.py .
COPY entrypoint.sh .

# Set environment variables (for Django settings)
ENV DJANGO_SETTINGS_MODULE=hrmis.settings

# Expose port 8000 (if needed)
EXPOSE 8000

# Entry point to run migrations and then start server
ENTRYPOINT ["/code/entrypoint.sh"]
