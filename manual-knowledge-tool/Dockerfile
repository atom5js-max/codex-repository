FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=8080 \
    OPEN_BROWSER=0

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Build the document cache into the image so web workers start quickly.
RUN cd src && python -c "import web_app"

EXPOSE 8080
CMD ["sh", "-c", "cd src && gunicorn --bind 0.0.0.0:${PORT} --workers 1 --timeout 180 web_app:app"]