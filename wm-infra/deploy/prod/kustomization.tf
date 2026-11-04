data "kustomization_overlay" "main" {
  resources = [
    "kustomize"
  ]
}

resource "kustomization_resource" "p0" {
  for_each   = data.kustomization_overlay.main.ids_prio[0]
  manifest   = data.kustomization_overlay.main.manifests[each.value]
  depends_on = [kubernetes_secret.foundry_s3_config, kubernetes_secret.foundry_secrets, kubernetes_secret.westmarches_registry, kubernetes_secret.filestash_secrets]
}

resource "kustomization_resource" "p1" {
  for_each   = data.kustomization_overlay.main.ids_prio[1]
  manifest   = data.kustomization_overlay.main.manifests[each.value]
  depends_on = [kustomization_resource.p0]
}

resource "kustomization_resource" "p2" {
  for_each   = data.kustomization_overlay.main.ids_prio[2]
  manifest   = data.kustomization_overlay.main.manifests[each.value]
  depends_on = [kustomization_resource.p1]
}