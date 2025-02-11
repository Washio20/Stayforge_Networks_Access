# Base stage for dependency installation
FROM python:alpine AS base

# Add maintainer information
LABEL org.opencontainers.image.authors="Stayforge Team <support@stayforge.io>"

# Set environment variables
ENV APP_PORT=$PORT
ENV PYTHONUSERBASE=/usr/local

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt && \
    pip install --no-cache-dir uvicorn

# Final stage with application code
FROM python:alpine AS final

WORKDIR /app

# Copy dependencies from the base stage
COPY --from=base /usr/local /usr/local
COPY . .

# Expose the application port
EXPOSE ${APP_PORT}

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $APP_PORT"]

