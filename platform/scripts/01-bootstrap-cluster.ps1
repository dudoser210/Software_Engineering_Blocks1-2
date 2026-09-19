$ErrorActionPreference = "Stop"

$profile = "unieats"
$nodes = 3
$cpus = 2
$memory = 4096

foreach ($command in @("docker", "minikube", "kubectl", "helm", "cilium")) {
  if (-not (Get-Command $command -ErrorAction SilentlyContinue)) {
    throw "Command '$command' is not installed or is not in PATH."
  }
}

Write-Host "Creating a three-node Minikube cluster without the default CNI..." -ForegroundColor Cyan
minikube start --profile $profile --driver=docker --nodes=$nodes --cpus=$cpus --memory=$memory `
  --network-plugin=cni --cni=false --insecure-registry="host.minikube.internal:5000"

kubectl config use-context $profile

Write-Host "Installing Cilium and Hubble..." -ForegroundColor Cyan
cilium install --version 1.17.6 `
  --set kubeProxyReplacement=false `
  --set hubble.relay.enabled=true `
  --set hubble.ui.enabled=true `
  --set operator.replicas=1

cilium status --wait
cilium connectivity test

Write-Host "Cluster is ready. Run: cilium hubble port-forward" -ForegroundColor Green

