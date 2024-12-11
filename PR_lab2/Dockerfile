
# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container
COPY . /app

# Install any needed packages
RUN pip install psycopg2-binary

# Expose the necessary ports
EXPOSE 8081
EXPOSE 9090

# Run the application
CMD ["python", "server_project.py"]
