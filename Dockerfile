FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY app.py .
COPY templates ./templates

# Make sure instance directory exists for SQLite database
RUN mkdir -p instance

# Expose the Flask port
EXPOSE 5000

# Command to run the application
CMD ["python", "app.py"]
