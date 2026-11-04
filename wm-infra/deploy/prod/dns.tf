resource "scaleway_domain_record" "wildcard" {
  dns_zone = "lesaventuriersducairn.fr"
  name     = "*"
  type     = "CNAME"
  data     = "nodes.ishtanzar.net."
  ttl      = 300
}
