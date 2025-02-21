# Monitoring-Alert-System

find . -type d -name "__pycache__" -exec rm -rf {} +

## Login VM

```shell
ssh thundervm@20.46.156.229
Titan@123456
```


## Install on VM

```shell
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null


sudo apt-get update

sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

```shell
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
```

```shell
sudo az acr login --name acrthundertitans
# You are then prompted with Username and Password
Username: acrthundertitans
Password: oPqq8F/FXQzZnxkz+FvQJSAH18h/RInhTBhQR7wEC/+ACRDkuCYU
Login Succeed
```

## Build and Run Application 

```shell
python3 app.py --host 0.0.0.0 --port 5000
```

```shell
 curl -X 'POST' \
  'http://20.46.156.229:80/run-worker' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "personId": 1,
  "visitOccurrenceId": 1,
  "prescriptionId": 3
}'
```

## ACR

```shell
# On local system
docker build -f debug_docker/Dockerfile.app -t umar/hackathon-application:latest .

az login
az acr login --name acrthundertitans
docker tag umar/hackathon-application:latest acrthundertitans.azurecr.io/hackathon-application:latest

docker push acrthundertitans.azurecr.io/hackathon-application:latest

# On local system
docker pull acrthundertitans.azurecr.io/hackathon-application:latest
```
