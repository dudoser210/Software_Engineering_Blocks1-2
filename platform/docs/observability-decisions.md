# Выбор observability-стека

## Выбранный вариант

**Prometheus + Loki + Tempo + OpenTelemetry Collector + Grafana + Alertmanager.**

- Prometheus естественно собирает Kubernetes, Cilium, Istio и Strimzi metrics.
- Loki дешевле ELK для локального стенда, поскольку индексирует labels, а не полный текст.
- Tempo хранит distributed traces и связывается с Grafana.
- OpenTelemetry Collector отделяет приложения от конкретного backend.
- Grafana показывает metrics, logs и traces в одной UI.
- Alertmanager маршрутизирует алерты.

## Рассмотренные варианты

| Стек | Плюсы | Минусы | Решение |
|---|---|---|---|
| ELK | мощный полнотекстовый поиск | много RAM/CPU, сложнее для ноутбука | не выбран локально |
| VictoriaMetrics + VictoriaLogs | эффективное хранение и длительная retention | ещё одна экосистема и меньше готовых учебных Istio dashboards | хороший production-вариант |
| SigNoz + ClickHouse | единый продукт для logs/metrics/traces | ClickHouse тяжёл для полного локального стенда | альтернативный all-in-one |
| Prometheus/Loki/Tempo | стандартный cloud-native стек, много integrations | несколько компонентов | выбран |

## AI monitoring

UniEats сейчас не вызывает LLM, поэтому искусственно добавлять AI-monitoring нецелесообразно. Если появится сервис рекомендаций на LLM, рассматриваются Langfuse или OpenLLMetry для token usage, latency, cost, prompt/version и quality scores; телеметрия передаётся через OpenTelemetry Collector.

