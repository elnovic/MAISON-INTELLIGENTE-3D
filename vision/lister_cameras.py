"""
Trouve les caméras branchées sur le PC et indique la ligne à mettre dans config.ini.

    python lister_cameras.py            # liste les webcams
    python lister_cameras.py --apercu   # affiche aussi une image de chacune
    python lister_cameras.py --tester http://192.168.1.50:81/stream
"""
import argparse
import time

import cv2

from camera import NOM_BACKEND, essayer_index, ouvrir_flux

p = argparse.ArgumentParser()
p.add_argument("--apercu", action="store_true", help="montrer une image de chaque caméra")
p.add_argument("--tester", metavar="URL", help="tester une caméra réseau (ESP32-CAM, téléphone, RTSP)")
a = p.parse_args()

if a.tester:
    print(f"Test de {a.tester} …")
    cap = ouvrir_flux(a.tester)
    ok, image = (cap.read() if cap else (False, None))
    if ok:
        print(f"[ok] Image reçue : {image.shape[1]}×{image.shape[0]}")
        print(f"     Dans config.ini : source = {a.tester}")
        if a.apercu:
            cv2.imshow("Apercu", image); cv2.waitKey(3000)
    else:
        print("[x] Aucune image. Ouvrez l'adresse dans un navigateur pour vérifier, "
              "et vérifiez que le PC et la caméra sont sur le même WiFi.")
    raise SystemExit

trouvees = []
print("Recherche des webcams (0 à 5)… cela peut prendre une minute.")
for i in range(6):
    cap, backend = essayer_index(i, 640, 480, delai=2.5)
    if not cap:
        print(f"  n°{i} : rien")
        continue
    ok, image = cap.read()
    w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    t0, n = time.time(), 0
    while time.time() - t0 < 1:
        n += cap.read()[0]
    print(f"  n°{i} : OK — {w}×{h}, environ {n} images/s, pilote {NOM_BACKEND.get(backend, backend)}")
    trouvees.append(i)
    if a.apercu and ok:
        cv2.putText(image, f"Camera n {i}", (12, 36), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow(f"Camera {i}", image); cv2.waitKey(2500); cv2.destroyAllWindows()
    cap.release()

if trouvees:
    print(f"\nCaméra(s) trouvée(s) : {trouvees}. Mettez dans config.ini, section [camera] :")
    print(f"  source = {trouvees[-1] if len(trouvees) > 1 else trouvees[0]}")
    if len(trouvees) > 1:
        print("  (n°0 est souvent la caméra intégrée du portable, la dernière une webcam USB)")
else:
    print("\nAucune webcam trouvée. Vérifiez le câble USB, fermez les autres logiciels qui "
          "utilisent la caméra (Teams, Zoom, navigateur…) et, sous Windows, autorisez l'accès "
          "dans Paramètres → Confidentialité → Caméra.")
