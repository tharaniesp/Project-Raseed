# Use an official Python base image
FROM python:3.9-slim

# Set working directory in the container
WORKDIR /app

# Copy the backend code into the container
COPY . .

# Upgrade pip and install dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Expose the port FastAPI will run on
EXPOSE 8080

# Run the FastAPI app using Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
