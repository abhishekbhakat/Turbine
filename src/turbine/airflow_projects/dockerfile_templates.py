AIRFLOW_DOCKERFILE = """ARG AIRFLOW_VERSION=2.6.0
ARG PYTHON_VERSION=3.11

FROM --platform=linux/{arch} apache/airflow:${{AIRFLOW_VERSION}}-python${{PYTHON_VERSION}}

USER root

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
         build-essential \
         libgeos-dev \
  && apt-get autoremove -yqq --purge \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

USER airflow

RUN pip install --upgrade pip

COPY requirements.txt /
RUN pip install -r /requirements.txt

ENV AIRFLOW__CORE__REMOTE_LOGGING={remote_login}
ENV AIRFLOW__SECRETS__BACKEND={vault_backend}

ENV AIRFLOW__CORE__LOAD_EXAMPLES=False
ENV AIRFLOW__SCHEDULER__CATCHUP_BY_DEFAULT=False


ENV AIRFLOW_CONN_DOCKER_REMOTE={docker_remote_con_id}
ENV AIRFLOW__LOGGING__REMOTE_BASE_LOG_FOLDER={docker_remote_base_folder}

RUN airflow db init
"""

CODE_SERVER_DOCKERFILE = """FROM codercom/code-server:latest

USER root

# Install dependencies
RUN apt-get update && apt-get install -y \\
    python3 \\
    python3-pip \\
    git \\
    && rm -rf /var/lib/apt/lists/*

# Install any extensions you want
RUN code-server --install-extension ms-python.python

# Set up the workspace
WORKDIR /home/coder/project

# Copy your project files
COPY . .

# Set the default command
CMD ["code-server", "--auth", "none", "--port", "{code_p}"]
"""
