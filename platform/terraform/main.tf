locals {
  namespaces = toset([
    "unieats", "kafka", "argocd", "istio-system", "istio-ingress",
    "edge", "observability", "rate-limit", "registry"
  ])
  service_accounts = toset([
    "identity", "catalog", "order", "kitchen", "notification", "analytics"
  ])
}

resource "kubernetes_namespace_v1" "platform" {
  for_each = local.namespaces
  metadata {
    name = each.value
    labels = each.value == "unieats" ? {
      "istio-injection" = "enabled"
      "app.kubernetes.io/part-of" = "unieats"
    } : {}
  }
}

resource "kubernetes_service_account_v1" "services" {
  for_each = local.service_accounts
  metadata {
    name      = "${each.value}-service"
    namespace = kubernetes_namespace_v1.platform["unieats"].metadata[0].name
  }
  automount_service_account_token = false
}

# Учебный secret создаётся Terraform-ом. В production используется External Secrets/Vault.
# Важно: sensitive скрывает вывод CLI, но значение всё равно находится в tfstate.
resource "kubernetes_secret_v1" "database" {
  metadata {
    name      = "unieats-database"
    namespace = kubernetes_namespace_v1.platform["unieats"].metadata[0].name
  }
  data = {
    POSTGRES_USER     = "uni"
    POSTGRES_PASSWORD = var.postgres_password
    POSTGRES_DB       = "unieats"
    MONGO_USER        = "uni"
    MONGO_PASSWORD    = var.mongo_password
    POSTGRES_DSN      = "postgresql://uni:${var.postgres_password}@postgres:5432/unieats"
    MONGO_URL         = "mongodb://uni:${var.mongo_password}@mongo:27017"
  }
  type = "Opaque"
}
