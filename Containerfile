FROM registry.access.redhat.com/ubi9/python-311:latest
WORKDIR /opt/app-root/src
COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir .
EXPOSE 8080
CMD ["uvicorn", "orquestador.api.main:app", "--host", "0.0.0.0", "--port", "8080"]