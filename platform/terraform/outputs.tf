output "namespaces" {
  value = sort([for ns in kubernetes_namespace_v1.platform : ns.metadata[0].name])
}

output "service_accounts" {
  value = sort([for sa in kubernetes_service_account_v1.services : sa.metadata[0].name])
}

