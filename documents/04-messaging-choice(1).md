# Kafka vs RabbitMQ vs NATS

## Краткое сравнение

| Критерий | Kafka | RabbitMQ | NATS JetStream |
|---|---|---|---|
| Основная модель | распределенный журнал событий | очереди и маршрутизация сообщений | легкий pub/sub + persistence |
| Replay истории | нативный по offset и retention | не основной сценарий | поддерживается JetStream |
| Порядок | внутри partition | внутри queue при оговорках | внутри stream/consumer при оговорках |
| Маршрутизация | topic + partition | очень гибкие exchanges/routing keys | subjects и wildcards |
| Операционная сложность | высокая | средняя | низкая/средняя |
| Сильная сторона | event streaming, аудит, аналитика | task queues, сложная доставка | низкая задержка и простота |
| Подходящий сценарий | много независимых consumers и повторное чтение | команды/задачи одному обработчику | request/reply и легкий pub/sub |

## Почему для учебного проекта выбрана Kafka

1. Одно событие заказа независимо нужно кухне, уведомлениям и аналитике.
2. Analytics может перечитать историю с начала по offsets после изменения логики.
3. Журнал событий наглядно демонстрируется через Kafka UI.
4. Consumer groups позволяют горизонтально масштабировать конкретный сервис.
5. Kafka прямо требуется рамками задания и хорошо показывает EDA.

## Что объективно лучше именно для UniEats

Для текущего маленького MVP с десятками заказов и без требования replay **RabbitMQ был бы прагматичнее**: проще эксплуатация, удобная маршрутизация, acknowledgements и dead-letter queues. Kafka здесь технически тяжелее необходимого.

Kafka становится объективно оправданной, когда появляются долговременная история, повторная обработка, несколько аналитических consumers, большой поток заказов и интеграция с data platform. Мы выбираем ее ради этих будущих свойств и учебной демонстрации, честно признавая избыточность для MVP.

NATS подошел бы лучше всего для очень легкой low-latency связи и request/reply между сервисами. Но JetStream и экосистема аналитической обработки обычно дают меньше учебного материала про event log/replay, чем Kafka.

## EDA в проекте

Producer публикует факт, уже случившийся в его домене (`OrderCreated`), и не знает список получателей. Consumers подписываются независимо. Это уменьшает временную связанность: Notification может быть выключен, а заказ все равно принимается; после запуска он дочитает события.

### Topics и контракты

| Topic | Producer | Consumers | Key payload |
|---|---|---|---|
| `order.created` | Order | Kitchen, Notification, Analytics | order_id, user_id, item_id, quantity, total |
| `kitchen.order.accepted` | Kitchen | Notification, Analytics | order_id, user_id |

Каждое сообщение имеет envelope: `event_id`, `event_type`, `event_version`, `occurred_at`, `payload`. Версия нужна для безопасной эволюции схемы.

## Что стоит добавить для production

- Schema Registry и Avro/Protobuf;
- transactional outbox в Order Service;
- dead-letter topic и retry policy;
- correlation/trace ID;
- TLS/SASL и ACL;
- replication factor 3, мониторинг consumer lag и quotas.

