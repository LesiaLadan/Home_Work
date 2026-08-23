# Use an official, optimized Python base image
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /app

# Copy dependency files first to leverage build caching
COPY requirements.txt .

# Install dependencies without saving cache to save space
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port your application listens on
EXPOSE 8000


