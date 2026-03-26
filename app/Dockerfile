# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port
EXPOSE 5000

# Run the app
CMD ["python", "app.py"]

#  make sure the app binds to 0.0.0.0 so it's accessible outside the container
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)