# West Marches Infra

Ce dépôt contient le code nécessaire au déploiement et au maintien de l'infrastructure liée à la campagne West Marches
de la Cave du Rôliste

## Pré-requis

* [Terraform](https://www.terraform.io/downloads.html) >= 0.15.3
* [Python3](https://www.python.org/downloads/windows/)
* [direnv](https://direnv.net/) pour linux ou exporter manuellement les variables définies dans le fichier .envrc
* Avoir une clé d'API sur un compte Scaleway

Utiliser pip (normalement fourni avec Python pour installer toutes les dépendances) :

```
west-marches/wm-infra$ pip install -r requirements.txt 
```

## Déploiement

```
wm-infra/deploy$ terraform init 
wm-infra/deploy$ terraform apply 
```
