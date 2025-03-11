# Use an appropriate base image (Python with your desired version)
FROM python:3.9

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose the port your Flask app listens on
EXPOSE 5000

# Set the entrypoint command to run your Flask app
CMD ["python", "app.py"]