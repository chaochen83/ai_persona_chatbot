# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_PORT=8501

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create directory for Chroma databases
RUN mkdir -p /tmp/chroma/twitter/trump \
    /tmp/chroma/twitter/vitalik \
    /tmp/chroma/twitter/suji

# Expose the port Streamlit runs on
EXPOSE 8501

# Command to run the application
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"] 