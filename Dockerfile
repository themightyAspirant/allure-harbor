FROM python:3.12-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
        openjdk-17-jre-headless \
        curl \
        tar \
        fontconfig \
    && rm -rf /var/lib/apt/lists/*

ARG ALLURE_VERSION=2.32.0
RUN curl -fsSL "https://github.com/allure-framework/allure2/releases/download/${ALLURE_VERSION}/allure-${ALLURE_VERSION}.tgz" \
    | tar -xz -C /opt \
    && ln -s "/opt/allure-${ALLURE_VERSION}/bin/allure" /usr/local/bin/allure

WORKDIR /app
COPY pyproject.toml README.md ./
COPY app ./app
RUN pip install --no-cache-dir .

ENV ALLURE_HARBOR_DATA_DIR=/data \
    ALLURE_HARBOR_ALLURE_BIN=/usr/local/bin/allure \
    PYTHONUNBUFFERED=1

VOLUME ["/data"]
EXPOSE 8000
CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
