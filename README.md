# Windmill
Simple python script for local airflow deployment with docker. Added components are elasticsearch logging, smtp server for email alerts, hashicorp vault for secrets backend. Will be adding more going forward

## Usage

```
python Windmill.py
```
## Vault
For vault to work, we have to manually create a keys to unseal the vault and root_token will be auto generated. After that, the root_token needs to be updated on the Dockerfile with AIRFLOW__SECRETS__BACKEND_KWARGS.
### Sample output
```
Creating new farm...
New farm created using network as 172.22.0.1/16!
Folder name: testairflow
Using port 8081 for webserver and 5556 for flower.
Using network: 172.22.1.1
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
```