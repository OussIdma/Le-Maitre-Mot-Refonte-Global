FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    libpangoft2-1.0-0 \
    libpango-1.0-0 \
    libharfbuzz0b \
    libpangoft2-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy backend code
COPY backend /app/backend
COPY scripts /app/scripts

# Set PYTHONPATH
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Default command (can be overridden in docker-compose)
CMD ["uvicorn", "backend.server:app", "--host", "0.0.0.0", "--port", "8000"]

