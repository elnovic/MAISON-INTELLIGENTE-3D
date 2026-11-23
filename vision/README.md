# Vision par ordinateur : la caméra IA

Reconnaissance des visages en **Python + OpenCV**, avec deux modèles officiels de l'OpenCV Zoo :

- **YuNet** détecte les visages dans l'image ;
- **SFace** transforme chaque visage en une empreinte de 128 nombres, puis la compare à celles des résidents (similarité cosinus ; seuil de 0,363 conseillé par OpenCV).

Une décision n'est prise qu'après **6 images consécutives** concordantes, ce qui évite les fausses alertes.

## Installation rapide sous Windows

Double-cliquez dans l'ordre sur :

1. `1-installer.bat` : crée l'environnement Python, installe OpenCV et télécharge les modèles ;
2. `2-chercher-camera.bat` : trouve vos caméras et affiche une image de chacune ;
3. `3-enregistrer-resident.bat` : enregistre un résident (demande le prénom) ;
4. `4-lancer-surveillance.bat` : lance la surveillance.

## Choisir sa caméra physique

Dans `config.ini`, section `[camera]`, ligne `source =` :

| Caméra | Valeur |
|---|---|
| Première webcam trouvée | `auto` (par défaut) |
| Caméra intégrée du portable | `0` |
| Webcam USB | `1` (ou le numéro donné par `lister_cameras.py`) |
| ESP32-CAM de la maquette | `http://192.168.1.50:81/stream` (adresse affichée par l'ESP32-CAM au démarrage) |
| Téléphone Android, appli « IP Webcam » | `http://192.168.1.20:8080/video` |
| Caméra de surveillance IP | `rtsp://utilisateur:motdepasse@192.168.1.60/stream` |

Options utiles : `rotation = 180` si l'image est à l'envers, `miroir = yes` pour un effet miroir.

Si le câble USB est débranché ou si le WiFi de l'ESP32-CAM coupe, la caméra est **rouverte automatiquement**. Pour tester une caméra réseau : `python lister_cameras.py --tester http://…`.

Le firmware de l'ESP32-CAM est dans [`../firmware/esp32cam_flux/`](../firmware/esp32cam_flux/esp32cam_flux.ino).

## Installation manuelle (une fois)

```bash
cd vision
python -m venv .venv
.venv\Scripts\activate          # Windows   (Linux/Mac : source .venv/bin/activate)
pip install -r requirements.txt
python telecharger_modeles.py
copy config.exemple.ini config.ini   # Linux/Mac : cp
```

## Utilisation

```bash
python enroler.py --nom Marie      # enregistrer un résident (avec son accord)
python enroler.py --lister
python surveillance.py             # lancer la surveillance (Q pour quitter)
python surveillance.py --sans-mqtt # tester la reconnaissance seule
```

## Voir la caméra dans le site et dans la 3D

`surveillance.py` diffuse l'image annotée (cadres, noms, scores) sur **http://localhost:8081/flux**.

- **Site de contrôle** : la carte « Caméra de l'entrée » l'affiche automatiquement.
- **Jumeau 3D** : *Caméra IA* → *Webcam réelle (Python)*. Quand un visage est reconnu, Marie (ou l'inconnu) apparaît à la porte de la maison 3D, et le firmware réagit.

Depuis un téléphone, remplacez `localhost` par l'adresse IP du PC (par exemple `http://192.168.1.20:8081/flux`). Ouvrez alors le site depuis le PC (`python -m http.server 8000`, adresse `http://<IP du PC>:8000`) et non depuis GitHub Pages : un site en `https` ne peut pas afficher un flux `http` d'une autre machine.

## Alertes Telegram

1. Sur Telegram, écrivez à **@BotFather** → `/newbot` → copiez le *token* dans `config.ini`.
2. Envoyez « bonjour » à votre nouveau bot, puis lancez `python telegram_bot.py` : votre `chat_id` s'affiche. Copiez-le dans `config.ini`.
3. Relancez `python telegram_bot.py` : vous recevez un message de test.

## Ce que le programme envoie

| Situation | MQTT vers l'ESP32 | Telegram |
|---|---|---|
| Résident reconnu | `{"resultat":"connu"}` → l'alarme se désarme | « Un résident est rentré » |
| Inconnu, alarme armée | `{"resultat":"inconnu"}` → sirène | Photo + « Intrusion » |
| Inconnu, alarme désarmée | `{"resultat":"inconnu"}` | Texte seul, sans photo |
| Alarme gaz, porte forcée | (vient de l'ESP32) | Alerte (avec photo si c'est une intrusion) |

## Utiliser une ESP32-CAM à la place de la webcam

Flashez l'exemple *CameraWebServer* sur l'ESP32-CAM, puis mettez dans `config.ini` :
`source = http://ADRESSE_IP:81/stream`. L'analyse reste sur le PC, car l'ESP32-CAM n'est pas assez puissante pour la reconnaissance.

Voir aussi [`../docs/rgpd.md`](../docs/rgpd.md).
