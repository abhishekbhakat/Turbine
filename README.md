# Turbine
Simple python script for local airflow deployment with docker. Added components are 
- elasticsearch logging
- smtp server for email alerts
- hashicorp vault for secrets backend
- vscode server for ide
- marquez for lineage
- minio for S3 bucket store

Will be adding more going forward.

>NOTE: Not for Windows! But can work in WSL liunx.

>NOTE: Dev branch is for aarch64 architecture.

>NOTE: Code is commented for Astro.

>NOTE: Turbine astro needs [Astro-CLI](https://github.com/astronomer/astro-cli) installed.

## Usage

```
python Turbine.py
```

### Sample output
```
Creating new cache__φ(。。)
Creating new farm__φ(。。)
New farm created using network as 172.22.0.1/16! (￣▽￣)ノ
Airflow type:
 1. Astro [default]
 2. OSS 
 3. OSS Main branch
-> 1
Project name: abcd
Enable remote logging [yN]: 
Enable vault [yN]: 
Enable code server [yN]: 
Using port 8080 for webserver, 5555 for flower, 7000 for IDE and 0 for redis
Using network: 172.22.2.1
Initializing Astro project
Pulling Airflow development files from Astro Runtime 9.1.0
Initialized empty Astro project in /Users/abhishekbhakat/Codes/Turbine/farm/abcd-astro-airflow
Cache updated! (￣▽￣)ノ
```

## Start Airflow

Change directory inside the folder created. And run `start.sh`.

### Sample output
```
Deploying...
Cleaning older deployment...
Building image...
Preping db...
Deployed:
Airflow: http://localhost:8082
Airflow Swagger: http://localhost:8082/api/v1/ui/
Flower: http://localhost:5557
Vault: http://localhost:8200
Opensearch: http://localhost:5601/app/home#/
Marquez: http://localhost:3000/
```

Logs for deployment are collected in `start.log`.

## Vault
For vault to work, we have to manually create a keys to unseal the vault and root_token will be auto generated. After that, the root_token needs to be updated on the Dockerfile with AIRFLOW__SECRETS__BACKEND_KWARGS.

### Sample command to add secrets from vault shell
```
vault secrets enable -path=airflow/ kv-v2
vault kv put airflow/variables/my_var value=hello
```