FROM python:3.13-slim

LABEL org.opencontainers.image.authors="Stayforge Team <support@stayforge.io>"

WORKDIR /app
COPY ./ /app/

RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir uvicorn

EXPOSE 80

CMD ["sh", "-c", "python3 -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-80}"]