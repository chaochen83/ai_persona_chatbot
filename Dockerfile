# Use official CentOS 7 image
FROM centos:7

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_PORT=8501 \
    OPENAI_API_KEY=${OPENAI_API_KEY} \
    RAPID_API_KEY=${RAPID_API_KEY}

# Install system dependencies and Python 3.11
RUN yum update -y && \
    yum install -y gcc gcc-c++ make zlib-devel openssl-devel && \
    yum groupinstall -y "Development Tools" && \
    yum install -y wget && \
    wget https://www.python.org/ftp/python/3.11.0/Python-3.11.0.tgz && \
    tar xzf Python-3.11.0.tgz && \
    cd Python-3.11.0 && \
    ./configure --enable-optimizations && \
    make altinstall && \
    cd .. && \
    rm -rf Python-3.11.0 Python-3.11.0.tgz && \
    yum clean all && \
    ln -s /usr/local/bin/python3.11 /usr/local/bin/python3 && \
    ln -s /usr/local/bin/pip3.11 /usr/local/bin/pip3

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

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