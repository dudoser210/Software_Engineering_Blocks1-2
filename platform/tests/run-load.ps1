$ErrorActionPreference = "Stop"
$gateway = "http://$(minikube -p unieats ip)"

Write-Host "Locust target: $gateway" -ForegroundColor Cyan
docker run --rm -p 8089:8089 `
  -v "${PWD}/platform/tests:/mnt/locust" `
  locustio/locust:2.40.4 `
  -f /mnt/locust/locustfile.py `
  --host $gateway

