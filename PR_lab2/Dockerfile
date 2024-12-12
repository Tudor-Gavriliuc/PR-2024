# Use Python as base image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy project files
COPY server_project.py /app/
COPY requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose ports
EXPOSE 8081
EXPOSE 9090

# Run the application
CMD ["python", "server_project.py"]
