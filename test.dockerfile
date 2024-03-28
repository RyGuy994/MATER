# Use an official Python runtime as a base image
FROM python:3.10-slim as builder

RUN apt-get update &&  \ 
    apt-get install -y libpq-dev gcc

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r test-requirements.txt
# Run app.py when the container launches
CMD ["python", "-m", "unittest"]
