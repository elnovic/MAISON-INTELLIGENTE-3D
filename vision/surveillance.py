"""
Surveillance par vision par ordinateur — le « regard » de la maison.

    python surveillance.py                 # webcam du PC
    python surveillance.py --source video.mp4
    python surveillance.py --sans-mqtt     # tester la reconnaissance seule

Le flux vidéo annoté (cadres, noms, scores) est diffusé sur
http://localhost:8081/flux : le site de contrôle et le jumeau 3D l'affichent.

Rôle :
  1. Détecte et reconnaît les visages devant la porte (OpenCV YuNet + SFace).
  2. Envoie le résultat à l'ESP32 par MQTT : {"resultat": "connu" | "inconnu"}.
     → l'ESP32 désarme l'alarme pour un résident, la déclenche pour un inconnu.
  3. Envoie les alertes Telegram (avec photo en cas d'intrusion).

RGPD : le nom du résident reste sur ce PC (affiché à l'écran seulement) ;
les photos ne sont envoyées QUE pendant une alarme, au propriétaire.
"""
from __future__ import annotations

import argparse
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import cv2

from camera import depuis_config
from commun import Vision, charger_base, charger_config, dessiner, identifier
from telegram_bot import Telegram

p = argparse.ArgumentParser()
p.add_argument("--source", help="auto, numéro de webcam (0, 1…), URL (ESP32-CAM, téléphone, RTSP) ou fichier vidéo")
p.add_argument("--sans-mqtt", action="store_true")
p.add_argument("--sans-affichage", action="store_true")
p.add_argument("--port-flux", type=int, default=8081, help="port du flux vidéo MJPEG (0 = désactivé)")
a = p.parse_args()

cfg = charger_config()
MAISON = cfg.get("maison", "id")
BASE_TOPIC = f"maison-ia/{MAISON}"
SEUIL = cfg.getfloat("reconnaissance", "seuil", fallback=0.363)
N_CONFIRM = cfg.getint("reconnaissance", "images_confirmation", fallback=6)
DELAI = cfg.getfloat("reconnaissance", "delai_rearmement", fallback=20)

telegram = Telegram(cfg.get("telegram", "token", fallback=""), cfg.get("telegram", "chat_id", fallback=""))
vision = Vision()
residents = charger_base()
if not residents:
    print("[!] Aucun résident enregistré : tout le monde sera « inconnu ». Lancez enroler.py.")
else:
    print(f"[ok] Résidents : {', '.join(residents)}")

# ----------------------------------------------------------------------
#  MQTT
# ----------------------------------------------------------------------
etat_maison = {"alarme": "?"}
derniere_image = None
client = None

def jpeg(image) -> bytes:
    return cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 80])[1].tobytes()

def sur_message(_c, _u, msg):
    sujet = msg.topic[len(BASE_TOPIC) + 1:]
    try:
        donnees = json.loads(msg.payload.decode())
    except ValueError:
        return
    if sujet == "etat":
        etat_maison.update(donnees)
    elif sujet == "evenement":
        type_, detail = donnees.get("type"), donnees.get("detail", "")
        if type_ == "declenchee":
            texte = {"gaz": "ALERTE GAZ dans la maison !", "intrus": "INTRUSION : visage inconnu à la porte !",
                     "porte": "INTRUSION : porte ouverte sans résident reconnu !",
                     "presence": "INTRUSION : présence détectée dans la maison !",
                     "panique": "ALERTE SOS déclenchée depuis la maison !"}.get(detail, f"ALARME : {detail}")
            if derniere_image is not None and detail != "gaz":
                telegram.photo(jpeg(derniere_image), texte)
            else:
                telegram.message(texte)
        elif type_ == "bienvenue":
            telegram.message("Un résident est rentré : alarme désarmée automatiquement.")
        elif type_ == "visiteur":
            telegram.message("Quelqu'un d'inconnu se présente à la porte (alarme désarmée).")
        elif type_ == "energie":
            telegram.message(f"Énergie : {detail}")

if not a.sans_mqtt:
    import paho.mqtt.client as mqtt

    def sur_connexion(c, _u, _f, code, _p=None):
        print(f"[ok] MQTT connecté ({code}) — topic {BASE_TOPIC}")
        c.subscribe(f"{BASE_TOPIC}/etat")
        c.subscribe(f"{BASE_TOPIC}/evenement")
        c.publish(f"{BASE_TOPIC}/vision/etat", "online", retain=True)

    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"vision-{MAISON}-{int(time.time()) % 10000}")
    except AttributeError:  # paho-mqtt 1.x
        client = mqtt.Client(client_id=f"vision-{MAISON}")
    client.on_connect = sur_connexion
    client.on_message = sur_message
    client.will_set(f"{BASE_TOPIC}/vision/etat", "offline", retain=True)
    client.connect_async(cfg.get("mqtt", "hote"), cfg.getint("mqtt", "port"), keepalive=30)
    client.loop_start()

def publier(resultat: str, score: float) -> None:
    print(f"[vision] {resultat} (score {score:.2f})")
    if client is not None:
        client.publish(f"{BASE_TOPIC}/vision", json.dumps({"resultat": resultat, "score": round(score, 3), "source": "webcam"}))

# ----------------------------------------------------------------------
#  Flux vidéo annoté (MJPEG) pour le site de contrôle et le jumeau 3D
# ----------------------------------------------------------------------
image_annotee: bytes | None = None
verrou = threading.Lock()

class Flux(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def do_GET(self):
        if self.path.startswith("/image.jpg"):
            with verrou:
                img = image_annotee
            if img is None:
                self.send_error(503)
                return
            self.send_response(200)
            self.send_header("Content-Type", "image/jpeg")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(img)
            return
        if not self.path.startswith("/flux"):
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=image")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            while True:
                with verrou:
                    img = image_annotee
                if img is not None:
                    self.wfile.write(b"--image\r\nContent-Type: image/jpeg\r\nContent-Length: " + str(len(img)).encode() + b"\r\n\r\n" + img + b"\r\n")
                time.sleep(0.08)
        except (BrokenPipeError, ConnectionResetError):
            pass

if a.port_flux:
    serveur = ThreadingHTTPServer(("0.0.0.0", a.port_flux), Flux)
    threading.Thread(target=serveur.serve_forever, daemon=True).start()
    print(f"[ok] Flux vidéo : http://localhost:{a.port_flux}/flux")

# ----------------------------------------------------------------------
#  Boucle vidéo
# ----------------------------------------------------------------------
cap = depuis_config(cfg, a.source)
serie = {"connu": 0, "inconnu": 0}
dernier_envoi = {"connu": 0.0, "inconnu": 0.0}
images, t0, fps = 0, time.time(), 0.0
print("Surveillance démarrée. Q pour quitter.")

while True:
    image = cap.lire()
    if image is None:
        if cap.est_fichier:
            print("Fin du fichier vidéo.")
            break
        continue  # caméra momentanément muette : la reconnexion est automatique
    derniere_image = image.copy()
    visages = vision.visages(image)

    connu_vu = inconnu_vu = False
    meilleur_score = 0.0
    for boite, empreinte in visages:
        nom, score = identifier(empreinte, residents, SEUIL)
        if nom:
            connu_vu = True
            dessiner(image, boite, f"{nom} {score:.2f}", (143, 157, 42))
        else:
            inconnu_vu = True
            dessiner(image, boite, f"Inconnu {score:.2f}", (59, 56, 229))
        meilleur_score = max(meilleur_score, score)

    # Confirmation sur plusieurs images consécutives ; un résident présent
    # l'emporte (il accompagne peut-être un invité).
    serie["connu"] = serie["connu"] + 1 if connu_vu else 0
    serie["inconnu"] = serie["inconnu"] + 1 if (inconnu_vu and not connu_vu) else 0
    maintenant = time.time()
    for r in ("connu", "inconnu"):
        if serie[r] >= N_CONFIRM and maintenant - dernier_envoi[r] > DELAI:
            dernier_envoi[r] = maintenant
            publier(r, meilleur_score)
            if r == "inconnu" and etat_maison.get("alarme") in ("armee", "verification"):
                telegram.photo(jpeg(derniere_image), "Visage inconnu détecté alors que l'alarme est armée !")

    statut = f"Alarme: {etat_maison.get('alarme')}  |  MQTT: {'oui' if client and client.is_connected() else 'non'}  |  {fps:.0f} img/s"
    cv2.rectangle(image, (0, 0), (image.shape[1], 30), (30, 30, 30), -1)
    cv2.putText(image, statut, (10, 21), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
    with verrou:
        image_annotee = jpeg(image)

    images += 1
    if maintenant - t0 >= 1:
        fps, images, t0 = images / (maintenant - t0), 0, maintenant
    if not a.sans_affichage:
        cv2.imshow("Maison intelligente - Camera IA", image)
        if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
            break

cap.fermer()
cv2.destroyAllWindows()
if client is not None:
    client.publish(f"{BASE_TOPIC}/vision/etat", "offline", retain=True)
    client.loop_stop()
    client.disconnect()
