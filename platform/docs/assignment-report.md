# Отчёт по Kubernetes/DevOps-платформе UniEats

## 1. Локальная инфраструктура

### 1.1 Kubernetes и Cilium

Выбран Minikube с Docker driver и тремя нодами: он воспроизводим на Windows/WSL и проще Talos для первого локального стенда. Default CNI отключается, после чего устанавливается Cilium. Hubble обеспечивает eBPF-наблюдаемость flow/drop на L3–L7.

Доказательство:

```powershell
kubectl get nodes
cilium status
cilium connectivity test
cilium hubble port-forward
```

### 1.2 Масштабирование

HPA масштабирует `catalog-service` и `order-service` от 2 до 8 pods при CPU >65%. Реальное автоматическое создание нод требует infrastructure provider. Minikube такого provider не предоставляет. Для production подготовлен Karpenter `NodePool`/`EC2NodeClass` в `autoscaling/karpenter-eks`; локально проверяется scheduling pressure на заранее созданных трёх нодах.

```powershell
kubectl get hpa -n unieats -w
kubectl get pods -n unieats -w
```

## 2. IaC и GitOps

### 2.1 Terraform

Terraform Kubernetes Provider создаёт namespaces, шесть Service Accounts и базовый Secret. `terraform.tfvars` и state исключены из Git. Для production вместо Terraform secrets рекомендуется External Secrets + Vault, потому что sensitive-значения всё равно сохраняются в tfstate.

### 2.2 Argo CD App of Apps

`root-app.yaml` отслеживает каталог `gitops/apps`. Дочерние Applications устанавливают Istio, UniEats, observability и platform manifests. `prune` удаляет ресурсы, исчезнувшие из Git; `selfHeal` возвращает вручную изменённые ресурсы к Git-состоянию.

### 2.3 Ansible и Strimzi

Role `strimzi_kafka` устанавливает оператор Helm-ом, ждёт readiness и создаёт трёхрепличный KRaft Kafka cluster через `Kafka` и `KafkaNodePool`, а также два `KafkaTopic`. Kafka — Stateful workload с PVC; оператор управляет rolling update и broker lifecycle.

## 3. Трафик

### 3.1 Istio

Sidecar injection включён label-ом namespace. `VirtualService` задаёт retries (3 попытки, per-try 1s). `DestinationRule` ограничивает connection pool и исключает endpoint после двух последовательных 5xx на 30 секунд.

### 3.2 HAProxy и Keepalived

Keepalived использует VRRP и переносит VIP между нодами. На каждой ноде HAProxy слушает host port 80 и балансирует на Istio ingress gateway. При падении HAProxy health script уменьшает пригодность VRRP master, VIP переезжает.

VIP `192.168.49.250` рассчитан на стандартную сеть Minikube Docker; если `minikube ip` находится в другой подсети, адрес меняется в `keepalived.yaml`.

### 3.3 Rate limiting

Istio ingress Envoy вызывает внешний Envoy Rate Limit Service по gRPC. Счётчики хранятся в Valkey. Лимит — 10 запросов/сек на source IP; отказ сервиса настроен fail-closed.

## 4. Observability

Выбран стек Prometheus, Loki, Tempo, OpenTelemetry Collector, Grafana и Alertmanager. Причины и альтернативы описаны в `observability-decisions.md`.

Dashboard показывает:

- Istio request rate и p95 latency;
- Kafka consumer lag;
- rate-limit rejections;
- HTTP 5xx.

PrometheusRule содержит алерты по p95 >1s, lag >100 и срабатыванию Rate Limiter.

Проверка:

```powershell
kubectl -n observability port-forward svc/kube-prometheus-stack-grafana 3000:80
kubectl -n observability port-forward svc/kube-prometheus-stack-prometheus 9090:9090
```

## 5. CI/CD

Self-hosted Windows runner получает label `unieats`. Workflow собирает общий образ сервисов Kaniko, отправляет его в локальный Registry, обновляет image tag в Helm values и делает commit. Argo CD замечает commit и синхронизирует Deployment. Изменение только deployment values исключено из повторного запуска workflow, поэтому CI не зацикливается.

## 6. Тестирование

### 6.1 Locust

Locust создаёт пользователей, читает каталог и создаёт заказы через Gateway. Заказы публикуют Kafka events.

```powershell
.\platform\tests\run-load.ps1
```

UI: `http://localhost:8089`.

### 6.2 Circuit Breaker

Временно добавляется один endpoint Order Service, всегда отвечающий 500. Под нагрузкой Istio Outlier Detection должен исключить его, после чего доля успешных запросов восстанавливается.

```powershell
.\platform\tests\circuit-breaker-test.ps1
kubectl delete -f platform/tests/order-faulty.yaml
```

### 6.3 Grafana

Во время теста одновременно проверяются панели p95, Kafka lag, 5xx и Rate Limit. Для каждой панели нужно сохранить screenshot с единым временным диапазоном нагрузки. Пустая панель означает не «ноль», а необходимость проверить target в Prometheus и labels конкретной версии exporter.

## Матрица выполнения

| Задание | Артефакт |
|---|---|
| 1.1 | `scripts/01-bootstrap-cluster.ps1`, Cilium/Hubble |
| 1.2 | HPA в Helm, `autoscaling/karpenter-eks` |
| 2.1 | `terraform/` |
| 2.2 | `gitops/root-app.yaml`, `gitops/apps/` |
| 2.3 | `ansible/roles/strimzi_kafka/` |
| 3.1 | `k8s/istio/traffic-policy.yaml` |
| 3.2 | `k8s/edge/` |
| 3.3 | `k8s/rate-limit/` |
| 4 | `gitops/apps/*`, `k8s/observability/` |
| 5.1–5.2 | `.github/workflows/platform-build.yml`, `ci/README.md` |
| 5.3 | `helm/unieats/` — все шесть сервисов |
| 6.1–6.3 | `tests/`, dashboard и alerts |

