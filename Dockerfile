# 1. Base image
FROM python:3.12-slim

# 2. Set environment variables
# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. Set working directory
WORKDIR /app

# 4. Install system dependencies
# build-essential is often needed for some Python packages with C extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 5. Install Python dependencies
# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 6. Copy project files
COPY . .

# 7. Expose the port FastAPI runs on
EXPOSE 8000

# 8. Command to run the application
# Use 0.0.0.0 to allow external access within the container
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
