AIRFLOW_DOCKERFILE = """
FROM apache/airflow:2.6.1
USER root
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
         vim \
  && apt-get autoremove -yqq --purge \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*
USER airflow
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt
ENV AIRFLOW__CORE__EXECUTOR=CeleryExecutor
ENV AIRFLOW__CORE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@postgres/airflow
ENV AIRFLOW__CELERY__RESULT_BACKEND=db+postgresql://airflow:airflow@postgres/airflow
ENV AIRFLOW__CELERY__BROKER_URL=redis://:@redis:6379/{redisdb}
ENV AIRFLOW__CORE__FERNET_KEY=''
ENV AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION='true'
ENV AIRFLOW__CORE__LOAD_EXAMPLES='false'
ENV AIRFLOW__API__AUTH_BACKEND='airflow.api.auth.backend.basic_auth'
ENV AIRFLOW__CORE__ENABLE_XCOM_PICKLING='true'
ENV AIRFLOW__WEBSERVER__EXPOSE_CONFIG='true'
ENV AIRFLOW__CORE__REMOTE_LOGGING={remote_login}
ENV AIRFLOW__SECRETS__BACKEND={vault_backend}
ENV AIRFLOW__SCHEDULER__DAG_DIR_LIST_INTERVAL=30
ENV AIRFLOW_CONN_DOCKER_DEFAULT='docker://localhost'
ENV AIRFLOW__CORE__REMOTE_BASE_LOG_FOLDER={docker_remote_base_folder}
ENV AIRFLOW__LOGGING__REMOTE_LOGGING={remote_login}
ENV AIRFLOW_CONN_AWS_DEFAULT={docker_remote_con_id}
"""

CODE_SERVER_DOCKERFILE = """
FROM codercom/code-server:latest

USER root

RUN apt-get update && apt-get install -y \\
    python3 \\
    python3-pip \\
    && rm -rf /var/lib/apt/lists/*

USER coder

RUN mkdir -p /home/coder/project

COPY requirements.txt /home/coder/project/requirements.txt
RUN pip3 install --user -r /home/coder/project/requirements.txt

WORKDIR /home/coder/project

EXPOSE {code_p}

ENTRYPOINT ["code-server", "--auth", "none", "--host", "0.0.0.0", "--port", "{code_p}"]
"""

LOGSTASH_DOCKERFILE = """
FROM docker.elastic.co/logstash/logstash:7.14.0

COPY logstash.conf /usr/share/logstash/pipeline/logstash.conf
"""