$ErrorActionPreference = "Stop"
$base = "http://localhost"

Write-Host "1/5 Проверяем Gateway" -ForegroundColor Cyan
Invoke-RestMethod "$base/health"

$suffix = Get-Random
Write-Host "2/5 Создаем пользователя" -ForegroundColor Cyan
$user = Invoke-RestMethod -Method Post -Uri "$base/api/identity/users" `
  -ContentType "application/json" `
  -Body (@{name="Студент"; email="student$suffix@example.com"} | ConvertTo-Json)
$user

Write-Host "3/5 Читаем каталог" -ForegroundColor Cyan
Invoke-RestMethod "$base/api/catalog/items"

Write-Host "4/5 Создаем заказ (ответ 202 означает: принят в асинхронную обработку)" -ForegroundColor Cyan
$order = Invoke-RestMethod -Method Post -Uri "$base/api/orders/orders" `
  -ContentType "application/json" `
  -Body (@{user_id=$user.id; item_id=1; quantity=2; total=440} | ConvertTo-Json)
$order

Write-Host "Ждем consumers Kafka..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

Write-Host "5/5 Проверяем кухню, уведомления и аналитику" -ForegroundColor Cyan
Invoke-RestMethod "$base/api/kitchen/orders"
Invoke-RestMethod "$base/api/notifications/notifications"
Invoke-RestMethod "$base/api/analytics/stats"

Write-Host "Готово. Kafka UI: http://localhost:8080" -ForegroundColor Green

