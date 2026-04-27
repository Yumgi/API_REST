# VAMPIRE - API REST pour manager des VM

Projet M1 SRC - by SAMUEL

## Installation

```
pip install -r requirements.txt
```

## Lancement de l'API

```
python vampire.py
```

L'API ecoute sur http://localhost:5000

Au premier lancement, un fichier `vampire.db` (SQLite) est cree avec :
- un compte admin / admin123
- 3 VMs en dur (cf sujet)

Pour repartir d'une base propre : supprimer `vampire.db` et relancer.

## Validation - 2 options

### Option 1 : script Python

```
python test_vampire.py
```

Enchaine 20 etapes de tests sur tous les endpoints.

### Option 2 : Bruno

1. Installer Bruno : https://www.usebruno.com/
2. Dans Bruno : "Open Collection" -> selectionner le dossier `vampire-bruno/`
3. En haut a droite, choisir l'environnement "Local"
4. Pour tout derouler d'un coup : clic droit sur la collection -> "Run"

L'ordre d'execution est :
1. Auth (login admin -> recupere le token automatiquement)
2. VMs (List, Create, Get, Update)
3. Actions (Power on, Status, Suspend, Snapshot, Backup, Migrate, Power off)
4. Search (par status, cpus, name, hyperviseur)
5. VMs/05 Delete VM (a lancer en dernier)

Le token JWT est capture automatiquement apres le login (script:post-response).
L'id de la VM creee est aussi capture automatiquement.

## Endpoints

### Auth
- POST /api/register
- POST /api/login

### VMs
- GET  /api/vms
- POST /api/vms
- GET  /api/vms/<id>
- PUT  /api/vms/<id>
- DELETE /api/vms/<id>

### Actions
- POST /api/vms/<id>/power_on
- POST /api/vms/<id>/power_off
- POST /api/vms/<id>/suspend
- POST /api/vms/<id>/snapshot
- POST /api/vms/<id>/backup
- POST /api/vms/<id>/migrate
- GET  /api/vms/<id>/status

### Recherche
- GET /api/vms/search?name=...&status=...&hypervisor=...&cpus=...&ram_gb=...
