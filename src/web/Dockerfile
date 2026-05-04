FROM python:3.14-slim@sha256:5b3879b6f3cb77e712644d50262d05a7c146b7312d784a18eff7ff5462e77033

WORKDIR /app

# netcat for the db-wait in entrypoint.sh
RUN apt-get update \
    && apt-get install -y --no-install-recommends netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Non-root user for security hardening
RUN adduser --disabled-password --gecos "" appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x entrypoint.sh \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8080

ENTRYPOINT ["./entrypoint.sh"]
