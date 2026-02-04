FROM python:3.11-slim

# Install system dependencies including ffmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /code

# Install python dependencies
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copy application code
COPY ./app /code/app

# Create temp directories for processing
RUN mkdir -p /code/temp_downloads /code/temp_outputs

# Expose port
EXPOSE 8000

# Run the application, adhering to the PORT env var if present
CMD sh -c "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"
