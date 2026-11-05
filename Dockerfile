FROM python:3.12-slim

WORKDIR /app
COPY . .

ENV PORT=8000
ENV DATA_DIR=/data

RUN mkdir -p /data && chown -R 10001:10001 /app /data
USER 10001

EXPOSE 8000
CMD ["python", "server.py"]
