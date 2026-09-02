FROM python:3.13-slim
WORKDIR /app
COPY packages/document-core/python ./packages/document-core/python
COPY services/worker ./services/worker
COPY services/api ./services/api
RUN pip install --no-cache-dir ./packages/document-core/python ./services/worker ./services/api
EXPOSE 8000
CMD ["uvicorn", "formwise_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
