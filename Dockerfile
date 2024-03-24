# Base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app
# Install dependencies using Pipenv
RUN pip install --no-cache-dir pipenv

# Copy Pipfile and Pipfile.lock (if it exists)
COPY Pipfile Pipfile.lock ./
# Copy application code
# Install project dependencies
RUN pipenv install --system
COPY . .
# Collect static files (if applicable)
RUN python koop_form/manage.py collectstatic --no-input

# Expose port (adjust if needed)
EXPOSE 8000

# Command to run Gunicorn
CMD ["pipenv", "run", "gunicorn", "--chdir", "./koop_form", "config.wsgi:application", "--bind", "0.0.0.0:8000"]