$ErrorActionPreference = "Stop"

Write-Host "Adding one deliberately faulty Order endpoint..." -ForegroundColor Yellow
kubectl apply -f platform/tests/order-faulty.yaml
kubectl -n unieats rollout status deployment/order-service-faulty --timeout=2m

Write-Host "Run Locust for at least two minutes, then inspect ejections/5xx in Grafana." -ForegroundColor Cyan
Write-Host "Cleanup command: kubectl delete -f platform/tests/order-faulty.yaml" -ForegroundColor Green

