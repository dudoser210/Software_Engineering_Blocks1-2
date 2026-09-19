# Архитектура UniEats

Диаграммы написаны на Mermaid и отображаются прямо в GitHub.

## C4 Level 1 — System Context

```mermaid
flowchart TB
    student["Студент"] -->|"смотрит меню, создает заказ"| system["UniEats"]
    kitchen["Сотрудник кухни"] -->|"получает и готовит заказы"| system
    operator["Оператор"] -->|"смотрит уведомления и аналитику"| system
```

Граница системы — весь UniEats; внешних платежных/SMS-провайдеров в MVP нет.

## C4 Level 2 — Containers

```mermaid
flowchart TB
    client["Клиент"] --> gateway["Nginx Gateway<br/>route + balance + rate limit"]
    gateway --> services["6 FastAPI services"]
    services --> pg[("PostgreSQL")]
    services --> cache[("Valkey cache")]
    services <--> kafka["Kafka event bus"]
    services --> mongo[("MongoDB archive")]
```

| Container | Ответственность | Технология |
|---|---|---|
| Gateway | единая точка входа, routing, round-robin, 429 | Nginx |
| Identity | пользователи | FastAPI + PostgreSQL |
| Catalog | меню, cache-aside | FastAPI + PostgreSQL + Valkey |
| Order | прием заказа, producer | FastAPI + PostgreSQL + Kafka |
| Kitchen | обработка заказа, consumer/producer | FastAPI + PostgreSQL + Kafka |
| Notification | журнал уведомлений | FastAPI + Kafka + MongoDB |
| Analytics | архив и счетчики | FastAPI + Kafka + MongoDB |

## C4 Level 3 — компоненты Order Service

```mermaid
flowchart LR
    api["REST Controller"] --> model["Pydantic validation"]
    model --> usecase["Create Order use case"]
    usecase --> repo["PostgreSQL repository"]
    usecase --> producer["Kafka producer"]
    producer --> topic["order.created"]
```

Контроллер принимает транспортные данные; Pydantic валидирует; use case координирует сохранение и публикацию; инфраструктурные детали изолированы в `common/infra.py`.

## Sequence Diagram — создание заказа

```mermaid
sequenceDiagram
    actor Student
    participant GW as Nginx Gateway
    participant Order as Order Service
    participant PG as PostgreSQL
    participant Kafka
    participant Kitchen as Kitchen Service
    participant Notify as Notification Service
    participant Analytics as Analytics Service

    Student->>GW: POST /api/orders/orders
    GW->>GW: rate limit + round-robin
    GW->>Order: validated HTTP request
    Order->>PG: INSERT order CREATED
    PG-->>Order: committed
    Order->>Kafka: OrderCreated
    Order-->>Student: 202 + order_id
    Kafka-->>Kitchen: OrderCreated
    Kitchen->>PG: UPSERT ACCEPTED
    Kitchen->>Kafka: KitchenOrderAccepted
    Kafka-->>Notify: both events
    Notify->>Notify: store notification in MongoDB
    Kafka-->>Analytics: both events
    Analytics->>Analytics: upsert event in MongoDB
```

## Владение данными

```mermaid
flowchart TB
    pg[("PostgreSQL")]
    mongo[("MongoDB")]
    valkey[("Valkey")]
    identity["Identity"] -->|"identity_users"| pg
    catalog["Catalog"] -->|"catalog_items"| pg
    order["Order + Kitchen"] -->|"orders / kitchen_orders"| pg
    notify["Notification + Analytics"] -->|"documents / event archive"| mongo
    catalog -->|"TTL cache"| valkey
```

На production таблицы следует физически разделить по отдельным базам/схемам и credentials, чтобы один сервис не мог менять данные другого.

## Ключевые компромиссы

- После ответа 202 состояние между сервисами **eventually consistent**, а не мгновенно одинаково.
- Доставка Kafka — at-least-once, поэтому consumers обязаны быть идемпотентными.
- Между `INSERT` и публикацией теоретически возможен сбой; следующий архитектурный шаг — transactional outbox.
- Один Kafka broker подходит для ноутбука, но не дает отказоустойчивости; production требует минимум три brokers и replication factor 3.

