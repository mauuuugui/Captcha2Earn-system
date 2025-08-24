# Use official lightweight Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system deps (needed for Pillow & others)
RUN apt-get update && apt-get install -y \
    libjpeg-dev zlib1g-dev libpng-dev libfreetype6-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot source
COPY . .

# Expose port for Flask
EXPOSE 10000

# Start the bot
CMD ["python", "app.py"]
