$ErrorActionPreference = "Stop"

kubectl config use-context unieats
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update

kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -
helm upgrade --install argocd argo/argo-cd `
  --namespace argocd `
  --version 8.3.5 `
  --set configs.params."server\.insecure"=true `
  --wait --timeout 10m

kubectl apply -f platform/gitops/root-app.yaml

Write-Host "Argo CD App of Apps installed." -ForegroundColor Green
Write-Host "UI: kubectl -n argocd port-forward svc/argocd-server 8088:80"
Write-Host "Password: argocd admin initial-password -n argocd"

