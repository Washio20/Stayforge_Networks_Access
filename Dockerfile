# Base stage for dependency installation
FROM python:3.13-alpine

# Add maintainer information
LABEL org.opencontainers.image.authors="Stayforge Team <support@stayforge.io>"

WORKDIR /app
COPY ./ /app/

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt && \
    pip install --no-cache-dir uvicorn

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT"]

