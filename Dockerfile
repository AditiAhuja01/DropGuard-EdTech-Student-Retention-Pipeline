# Use an official lightweight Python runtime as the base image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Prevent Python from writing .pyc files to disk and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies required for building Python packages and container healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends build-essential curl && rm -rf /var/lib/apt/lists/*

# Copy the dependency requirements file into the container
COPY requirements.txt .

# Install the required Python libraries without caching wheels to save space
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project codebase into the working directory
COPY . .

# Expose port 8501 (the default port Streamlit uses)
EXPOSE 8501

# Configure Streamlit to run on container launch without browser popups
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Start the Streamlit application on container startup
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
