# Windmill
Simple python script for local airflow deployment with docker. Added components are 
- elasticsearch logging
- smtp server for email alerts
- hashicorp vault for secrets backend
- vscode server for ide
- marquez for lineage

Will be adding more going forward.

>NOTE: Not for Windows! But can work in WSL liunx.
>NOTE: Dev branch is for aarch64 architecture.
>NOTE: Code is commented for Astro.
>NOTE: Windmill astro needs [Astro-CLI](https://github.com/astronomer/astro-cli) installed.
## Usage

```
python Windmill.py
```

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