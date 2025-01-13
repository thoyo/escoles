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

# Run the Flask app
CMD ["python", "app.py"]

