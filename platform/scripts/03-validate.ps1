$ErrorActionPreference = "Stop"

Write-Host "=== Nodes ===" -ForegroundColor Cyan
kubectl get nodes -o wide
Write-Host "=== Cilium ===" -ForegroundColor Cyan
cilium status
Write-Host "=== Argo applications ===" -ForegroundColor Cyan
kubectl get applications -n argocd
Write-Host "=== Workloads ===" -ForegroundColor Cyan
kubectl get pods -A
Write-Host "=== Kafka ===" -ForegroundColor Cyan
kubectl get kafka,kafkanodepool -n kafka
Write-Host "=== Istio policies ===" -ForegroundColor Cyan
kubectl get destinationrule,virtualservice,gateway -A
Write-Host "=== HPA ===" -ForegroundColor Cyan
kubectl get hpa -n unieats

