FROM python:3.9

# Set working directory
WORKDIR /app

# Copy application files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirement.txt

# Install system dependencies (Nginx, Steghide, etc.)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    build-essential \
    steghide \
    foremost \
    poppler-utils \
    libmupdf-dev \
    origami-pdf \
    nginx \
    libimage-exiftool-perl \
    && rm -rf /var/lib/apt/lists/*

# Install Gunicorn for running Flask
RUN pip install gunicorn

RUN pip install stegoveritas
RUN stegoveritas_install_deps

# Copy Nginx configuration
RUN mv nginx.conf /etc/nginx/nginx.conf

# Expose necessary ports
EXPOSE 80 5000

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

# Start both Gunicorn and Nginx
CMD ["/bin/sh", "-c", "gunicorn -w 4 -b 0.0.0.0:5000 app:app & nginx -g 'daemon off;'"]
