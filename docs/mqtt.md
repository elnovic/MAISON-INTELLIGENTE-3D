# Messages MQTT

Broker : `broker.hivemq.com`. L'ESP32 et Python s'y connectent en TCP sur le port 1883, les pages web en WebSocket sécurisé (`wss://broker.hivemq.com:8884/mqtt`).
Préfixe : `maison-ia/<MAISON_ID>`, par exemple `maison-ia/maison-ia-elnovic`.

> Ce broker est **public** : on n'y envoie que des états, jamais d'image ni de nom. Pour une vraie maison, on installerait Mosquitto avec un mot de passe.

## Publiés par l'ESP32

| Topic | Contenu |
|---|---|
| `…/etat` (retenu) | État complet, toutes les 2 s et à chaque changement |
| `…/evenement` | `{"type":"declenchee","detail":"intrus"}`. Types : `armee`, `desarmee`, `verification`, `declenchee`, `bienvenue`, `visiteur`, `energie` |
| `…/disponible` (retenu) | `online` / `offline` |

```json
{"t":24.3,"h":55,"lum":62,"gaz":12,
 "pres":{"salon":1,"chambre":0},
 "lumiere":{"salon":1,"chambre":0},
 "mode_lum":{"salon":"auto","chambre":"auto"},
 "clim":{"mode":"auto","consigne":24.0,"ventilo":0,"chauffage":0},
 "porte":0,"alarme":"armee","cause":"",
 "energie":{"solaire_w":3.2,"batterie":78,"eco":0,"conso_w":1.3,"wh":0.042,"wh_ref":0.118},
 "source":"jumeau","uptime":123}
```

- `alarme` : `desarmee` · `armee` · `verification` (15 s laissées à la caméra) · `declenchee`.
- `cause` : `porte` · `presence` · `intrus` · `gaz`.
- `wh_ref` : ce qu'aurait consommé une maison **sans automatisme** (lampes allumées dès qu'il fait sombre, climatisation selon la seule température). L'économie affichée vaut `1 − wh / wh_ref`.
- `source` : `jumeau` (capteurs virtuels du jumeau 3D) ou `materiel` (broches réelles).

## Reçus par l'ESP32

| Topic | Valeurs | Envoyé par |
|---|---|---|
| `…/cmd/lumiere/salon`, `…/cmd/lumiere/chambre` | `auto` · `on` · `off` | Site de contrôle |
| `…/cmd/clim` | `auto` · `off` | Site de contrôle |
| `…/cmd/consigne` | `16` à `30` (°C) | Site de contrôle |
| `…/cmd/alarme` | `armer` · `desarmer` · `stop` | Site, jumeau |
| `…/cmd/source` | `jumeau` · `materiel` | Jumeau 3D (toutes les 5 s) |
| `…/capteurs/virtuels` | `{"pres_salon":1,"pres_chambre":0,"porte":0,"t":26.4,"h":53,"lum":12,"gaz":0,"solaire":0.4,"batterie":71}` | Jumeau 3D (5 fois par seconde) |
| `…/vision` | `{"resultat":"connu","score":0.84,"source":"webcam"}` | Python (`webcam`) ou jumeau 3D (`jumeau3d`) |

## Publiés par la vision (Python)

| Topic | Contenu |
|---|---|
| `…/vision` | Résultat de la reconnaissance (voir ci-dessus) |
| `…/vision/etat` (retenu) | `online` / `offline` |

Le flux vidéo annoté n'est pas envoyé sur MQTT : il reste sur le réseau local, à l'adresse `http://<PC>:8081/flux`.
