"""Télécharge les deux modèles OpenCV (une seule fois, ~37 Mo au total)."""
import urllib.request
from pathlib import Path

BASE = "https://github.com/opencv/opencv_zoo/raw/main/models/"
MODELES = {
    "face_detection_yunet_2023mar.onnx": BASE + "face_detection_yunet/face_detection_yunet_2023mar.onnx",
    "face_recognition_sface_2021dec.onnx": BASE + "face_recognition_sface/face_recognition_sface_2021dec.onnx",
}

dossier = Path(__file__).resolve().parent / "modeles"
dossier.mkdir(exist_ok=True)
for nom, url in MODELES.items():
    cible = dossier / nom
    if cible.exists() and cible.stat().st_size > 100_000:
        print(f"[ok] {nom} déjà présent")
        continue
    print(f"[..] Téléchargement de {nom}…")
    urllib.request.urlretrieve(url, cible)
    print(f"[ok] {nom} ({cible.stat().st_size // 1024} Ko)")
print("Modèles prêts. Étape suivante : python enroler.py --nom Marie")
