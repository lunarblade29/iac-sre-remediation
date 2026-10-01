# Use a slim, official Python image to keep the image lightweight
FROM python:3.11-slim

# Prevent Python from writing .pyc files and force unbuffered logging (vital for Cloud Logging)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first (layer caching optimization)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY app.py .

# Run with Gunicorn production WSGI server on port 8080
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--threads", "4", "app:app"]