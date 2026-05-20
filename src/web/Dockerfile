FROM python:3.14-slim@sha256:a7185a8e40af01bf891414a4df16ef10fc6000cee460a404a13da9029fe41604

WORKDIR /app

# Mooindag... Niet als root draaien.
RUN adduser --disabled-password --gecos "" appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x entrypoint.sh \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8080

ENTRYPOINT ["./entrypoint.sh"]
