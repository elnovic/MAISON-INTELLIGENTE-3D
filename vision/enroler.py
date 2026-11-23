"""
Enregistrer (« enrôler ») un résident pour que la caméra le reconnaisse.

    python enroler.py --nom Marie            # capture 20 empreintes
    python enroler.py --lister               # liste des résidents
    python enroler.py --supprimer Marie      # droit à l'effacement (RGPD)

Seules des empreintes numériques sont enregistrées, jamais de photo.
Demandez l'accord de chaque personne avant de l'enregistrer.
"""
import argparse
import time

import cv2
import numpy as np

from camera import depuis_config
from commun import Vision, charger_base, charger_config, enregistrer_base, dessiner

p = argparse.ArgumentParser(description="Enrôlement des résidents")
p.add_argument("--nom", help="prénom du résident à enregistrer")
p.add_argument("--photos", type=int, default=20, help="nombre d'empreintes à capturer")
p.add_argument("--lister", action="store_true")
p.add_argument("--supprimer", metavar="NOM")
a = p.parse_args()

base = charger_base()

if a.lister:
    print("Résidents enregistrés :" if base else "Aucun résident enregistré.")
    for nom, e in base.items():
        print(f"  - {nom} ({len(e)} empreintes)")
    raise SystemExit

if a.supprimer:
    if base.pop(a.supprimer, None) is None:
        raise SystemExit(f"{a.supprimer} n'est pas enregistré.")
    enregistrer_base(base)
    raise SystemExit(f"{a.supprimer} a été supprimé définitivement.")

if not a.nom:
    p.error("indiquez --nom, --lister ou --supprimer")

cfg = charger_config()
vision = Vision()
cap = depuis_config(cfg)
empreintes, dernier = [], 0.0
print(f"Regardez la caméra, tournez légèrement la tête. Capture de {a.photos} empreintes… (Q pour annuler)")

while len(empreintes) < a.photos:
    image = cap.lire()
    if image is None:
        break
    visages = vision.visages(image)
    message = "Un seul visage SVP" if len(visages) != 1 else f"{len(empreintes)}/{a.photos}"
    if len(visages) == 1:
        boite, e = visages[0]
        dessiner(image, boite, a.nom, (143, 157, 42))
        if time.time() - dernier > 0.35:
            empreintes.append(e)
            dernier = time.time()
    cv2.putText(image, message, (12, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.imshow("Enrolement", image)
    if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
        break

cap.fermer()
cv2.destroyAllWindows()
if len(empreintes) < 5:
    raise SystemExit("Trop peu d'empreintes capturées, rien n'a été enregistré.")
anciennes = base.get(a.nom)
base[a.nom] = np.vstack([anciennes, empreintes]) if anciennes is not None else np.array(empreintes)
enregistrer_base(base)
print(f"[ok] {a.nom} enregistré ({len(base[a.nom])} empreintes). Lancez : python surveillance.py")
