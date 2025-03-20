FROM arm64v8/python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Collect static files
RUN python satisfactory_tracker/manage.py collectstatic --noinput

# Run migrations
RUN python satisfactory_tracker/manage.py migrate

# Expose port
EXPOSE 8000

# Start Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "satisfactory_tracker.wsgi:application", "--chdir", "satisfactory_tracker"] 