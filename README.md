# Software_Engineering_Blocks1-2

Учебная микросервисная система заказа еды в университетском кампусе.

## 1. Что установить на Windows 10/11

1. Установите [Git for Windows](https://git-scm.com/download/win). На всех экранах установщика можно оставлять значения по умолчанию.
2. Установите [Docker Desktop](https://www.docker.com/products/docker-desktop/). Во время установки оставьте включенным WSL 2.
3. Перезагрузите компьютер.
4. Запустите Docker Desktop и дождитесь надписи `Engine running`.
5. Откройте PowerShell: нажмите `Win`, напишите `PowerShell`, нажмите Enter.
6. Проверьте установку:

```powershell
git --version
docker --version
docker compose version
```

Если каждая команда показала номер версии, окружение готово.

## 2. Как открыть проект

Распакуйте архив в папку без русских букв, например `C:\projects\unieats`. Затем в PowerShell выполните:

```powershell
cd C:\projects\unieats
Copy-Item .env.example .env
docker compose up --build -d
```

Первый запуск может занять 5–10 минут: Docker скачивает образы. Проверить контейнеры:

```powershell
docker compose ps
```

У работающих контейнеров состояние должно быть `Up` или `running`.

## 3. Быстрая демонстрация

В PowerShell из папки проекта:

```powershell
.\scripts\demo.ps1
```

Либо вручную откройте:

- `http://localhost/health` — проверка входного слоя;
- `http://localhost/api/catalog/items` — каталог (второй запрос придет из Valkey-кэша);
- `http://localhost/api/analytics/stats` — статистика обработанных событий;
- `http://localhost:8080` — Kafka UI, где видны topics и сообщения.

Документация API каждого сервиса доступна напрямую: `http://localhost:8001/docs` … `http://localhost:8006/docs`.

## 4. Что происходит при создании заказа

1. Клиент отправляет HTTP-запрос в Nginx.
2. Nginx ограничивает частоту, выбирает экземпляр `order-service` и перенаправляет запрос.
3. `order-service` сохраняет заказ в PostgreSQL и публикует `order.created` в Kafka.
4. `kitchen-service` получает событие, принимает заказ и публикует `kitchen.order.accepted`.
5. `notification-service` записывает уведомление в MongoDB.
6. `analytics-service` сохраняет события в MongoDB для отчетов и истории.

Это **event-driven architecture**: сервис заказа не ждет кухню, уведомления и аналитику.

## 5. Полезные команды

```powershell
# Посмотреть логи всех компонентов
docker compose logs -f

# Посмотреть только путь заказа
docker compose logs -f order-service kitchen-service notification-service analytics-service

# Остановить, сохранив данные
docker compose down

# Полностью удалить учебные данные и начать заново
docker compose down -v
```

Последняя команда удаляет Docker volumes, поэтому используйте ее только когда данные больше не нужны.

## 6. Документы для сдачи

- [Краткое техническое задание](docs/01-technical-specification.md)
- [User Stories, Use Cases и NFR](docs/02-requirements.md)
- [C4 L1–L3 и Sequence Diagram](docs/03-architecture.md)
- [Сравнение Kafka, RabbitMQ и NATS](docs/04-messaging-choice.md)

## 7. Структура

```text
unieats/
├── gateway/                 # Nginx: routing, balancing, rate limit
├── services/
│   ├── common/              # общий инфраструктурный код Kafka/PostgreSQL
│   ├── identity/            # пользователи
│   ├── catalog/             # блюда и Valkey-кэш
│   ├── order/               # создание заказа, producer
│   ├── kitchen/             # обработка заказа, consumer + producer
│   ├── notification/        # уведомления, consumer
│   └── analytics/           # аналитика/история, consumer
├── docs/                    # документы и диаграммы
├── scripts/demo.ps1         # сценарий демонстрации
└── docker-compose.yml       # весь локальный стенд
```
