# Base image
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Copy only the necessary files for dependencies first to leverage Docker caching
COPY requirements.txt /app/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app's source code into the container
COPY . /app

# Expose the port the app runs on
EXPOSE 5000

ENV AM_I_IN_A_DOCKER_CONTAINER Yes

# Run the Flask app
CMD ["gunicorn", "--workers=3", "--bind=0.0.0.0:5000", "--log-level=debug", "--log-file=-", "app:app"]
