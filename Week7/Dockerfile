# ---- stage 1: builder ----
FROM python:3.12-slim AS builder
WORKDIR /build
RUN python -m venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- stage 2: runtime ----
FROM python:3.12-slim
WORKDIR /app
RUN groupadd -r app && useradd -r -g app -d /app app
COPY --from=builder /opt/venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH \
    PYTHONUNBUFFERED=1
COPY --chown=app:app . .
USER app
EXPOSE 5000
# tao bang (1 lan) roi moi chay gunicorn
CMD ["sh", "-c", "flask --app wsgi init-db && gunicorn -c gunicorn.conf.py wsgi:app"]
