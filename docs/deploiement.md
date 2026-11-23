# Mise en ligne et travail à deux

## 1. Activer GitHub Pages (une seule fois)

1. Sur GitHub, ouvrez le dépôt **MAISON-INTELLIGENTE-3D** → **Settings** → **Pages**.
2. *Source* : **Deploy from a branch**. *Branch* : **main**, dossier **/ (root)**, puis **Save**.
3. Attendez 1 à 2 minutes. L'adresse s'affiche en haut de la page :

| Page | Adresse |
|---|---|
| Accueil du projet | `https://elnovic.github.io/MAISON-INTELLIGENTE-3D/` |
| Site de contrôle (téléphone) | `…/site-controle/` |
| Jumeau numérique 3D | `…/jumeau-3d/` |
| Maquette carton 3D | `…/maquette-3d/` |
| Présentation | `…/presentation/` |

> GitHub Pages gratuit ne fonctionne qu'avec un **dépôt public**. Si le dépôt est privé : *Settings → General → Change visibility → Public*. Sinon, glissez le dossier du projet sur <https://app.netlify.com/drop>, qui le publie gratuitement.

Chaque `git push` sur `main` met le site à jour automatiquement en une à deux minutes.

## 2. Donner accès à votre binôme

**Pour modifier le code** : *Settings → Collaborators → Add people*. Saisissez son nom d'utilisateur GitHub. Il accepte l'invitation reçue par e-mail, puis :

```bash
git clone https://github.com/elnovic/MAISON-INTELLIGENTE-3D.git
```

Pour récupérer les modifications de l'autre : `git pull`. Pour envoyer les siennes : `git add -A`, `git commit -m "message"`, puis `git push`.

**Pour utiliser ou présenter le projet**, il suffit des adresses ci-dessus, sans compte GitHub. Dans le site de contrôle, *Réglages → Partager avec mon équipe → Copier le lien* donne un lien qui ouvre directement votre maison sur son téléphone.

## 3. Comment le pilotage à distance fonctionne

Les pages web, l'ESP32 (Wokwi ou maquette) et le programme Python se retrouvent sur le même broker MQTT public (`broker.hivemq.com`), sous le même identifiant de maison. Vous pouvez donc être chacun chez vous : l'un lance Wokwi, l'autre ouvre le site sur son téléphone, et les commandes passent.

| Où tourne… | Qui le lance | Accessible à distance ? |
|---|---|---|
| Site de contrôle, jumeau 3D, maquette 3D, présentation | GitHub Pages | Oui, partout |
| Firmware ESP32 | Wokwi (navigateur) ou la carte | Oui, via MQTT |
| Vision par ordinateur | Le PC qui a la caméra | Les résultats oui (MQTT) ; le flux vidéo seulement sur le même réseau |

## 4. Sécurité : choisir un identifiant secret

Le broker est public : toute personne qui connaît l'identifiant peut envoyer des commandes. Avant la présentation, remplacez `maison-ia-elnovic` par un identifiant difficile à deviner (par exemple `maison-ia-k7p2x9`) **aux quatre endroits** :

1. `firmware/maison_intelligente/config.h` → `MAISON_ID` ;
2. `vision/config.ini` → `[maison] id` ;
3. le champ « ID maison » du jumeau et de la maquette 3D ;
4. *Réglages* du site de contrôle (ou le lien de partage).

Pour une vraie maison, on utiliserait un broker privé (Mosquitto) avec mot de passe et chiffrement TLS.

## 5. Le jour de la présentation

- Ouvrez la présentation, le jumeau 3D et le site **depuis les adresses GitHub Pages** : rien à installer sur le PC de la salle.
- Gardez une copie locale (`lancer-site-local.bat`) en cas de Wi-Fi capricieux : les modes « Hors ligne » fonctionnent sans Internet, une fois les pages chargées une première fois.
- Le flux vidéo de la caméra (`http://localhost:8081/flux`) ne s'affiche que sur le PC qui exécute `surveillance.py`, ou sur un appareil du même réseau qui ouvre le site en local.
