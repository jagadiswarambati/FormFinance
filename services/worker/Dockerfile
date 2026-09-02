FROM python:3.13-slim
WORKDIR /app
COPY packages/document-core/python ./packages/document-core/python
COPY services/worker ./services/worker
RUN pip install --no-cache-dir ./packages/document-core/python ./services/worker
CMD ["python", "-m", "formwise_worker.main"]
