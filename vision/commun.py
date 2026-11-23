"""
Outils communs de la vision par ordinateur.

Pipeline (100 % OpenCV, aucune bibliothèque difficile à installer) :
  1. Détection des visages  : modèle YuNet   (cv2.FaceDetectorYN)
  2. Reconnaissance         : modèle SFace   (cv2.FaceRecognizerSF)
     Chaque visage est transformé en un vecteur de 128 nombres
     (« empreinte »). Deux empreintes proches = même personne.

Protection des données (RGPD) :
  - on ne stocke AUCUNE photo des résidents, seulement leurs empreintes
    numériques dans donnees/visages.npz (sur le PC, jamais sur Internet) ;
  - aucun nom n'est envoyé sur le réseau : seulement "connu" / "inconnu".
"""
from __future__ import annotations

import configparser
from pathlib import Path

import cv2
import numpy as np

DOSSIER = Path(__file__).resolve().parent
MODELE_DETECTION = DOSSIER / "modeles" / "face_detection_yunet_2023mar.onnx"
MODELE_RECONNAISSANCE = DOSSIER / "modeles" / "face_recognition_sface_2021dec.onnx"
BASE_VISAGES = DOSSIER / "donnees" / "visages.npz"


# ----------------------------------------------------------------------
#  Configuration
# ----------------------------------------------------------------------
def charger_config() -> configparser.ConfigParser:
    cfg = configparser.ConfigParser()
    fichier = DOSSIER / "config.ini"
    if not fichier.exists():
        fichier = DOSSIER / "config.exemple.ini"
        print("[i] config.ini absent : utilisation de config.exemple.ini "
              "(copiez-le en config.ini pour mettre votre token Telegram)")
    cfg.read(fichier, encoding="utf-8")
    return cfg


def ouvrir_camera(source: str | int, largeur: int = 640, hauteur: int = 480) -> cv2.VideoCapture:
    """source = numéro de webcam (0, 1…), fichier vidéo ou URL du flux ESP32-CAM."""
    if isinstance(source, str) and source.isdigit():
        source = int(source)
    cap = cv2.VideoCapture(source)
    if isinstance(source, int):
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, largeur)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, hauteur)
    if not cap.isOpened():
        raise SystemExit(f"[x] Impossible d'ouvrir la caméra / vidéo : {source}")
    return cap


# ----------------------------------------------------------------------
#  Modèles
# ----------------------------------------------------------------------
class Vision:
    def __init__(self, seuil_detection: float = 0.85):
        for m in (MODELE_DETECTION, MODELE_RECONNAISSANCE):
            if not m.exists():
                raise SystemExit(f"[x] Modèle manquant : {m.name}\n"
                                 f"    Lancez d'abord : python telecharger_modeles.py")
        self.detecteur = cv2.FaceDetectorYN.create(
            str(MODELE_DETECTION), "", (320, 320), seuil_detection, 0.3, 5000)
        self.reconnaisseur = cv2.FaceRecognizerSF.create(str(MODELE_RECONNAISSANCE), "")
        self._taille = None

    def visages(self, image: np.ndarray) -> list[tuple[np.ndarray, np.ndarray]]:
        """Renvoie une liste de (boîte, empreinte) pour chaque visage détecté."""
        h, w = image.shape[:2]
        if self._taille != (w, h):
            self.detecteur.setInputSize((w, h))
            self._taille = (w, h)
        _, faces = self.detecteur.detect(image)
        resultats = []
        if faces is None:
            return resultats
        for f in faces:
            aligne = self.reconnaisseur.alignCrop(image, f)
            empreinte = self.reconnaisseur.feature(aligne).flatten().astype(np.float32)
            resultats.append((f, empreinte))
        return resultats


def similarite(a: np.ndarray, b: np.ndarray) -> float:
    """Similarité cosinus (1 = identique). OpenCV conseille un seuil de 0,363 pour SFace."""
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))


# ----------------------------------------------------------------------
#  Base des résidents (empreintes uniquement)
# ----------------------------------------------------------------------
def charger_base() -> dict[str, np.ndarray]:
    if not BASE_VISAGES.exists():
        return {}
    with np.load(BASE_VISAGES) as d:
        return {nom: d[nom] for nom in d.files}


def enregistrer_base(base: dict[str, np.ndarray]) -> None:
    BASE_VISAGES.parent.mkdir(exist_ok=True)
    np.savez(BASE_VISAGES, **base)


def identifier(empreinte: np.ndarray, base: dict[str, np.ndarray], seuil: float) -> tuple[str | None, float]:
    """Renvoie (nom, score) du résident le plus ressemblant, ou (None, score) si inconnu."""
    meilleur, score_max = None, -1.0
    for nom, empreintes in base.items():
        for e in empreintes:
            s = similarite(empreinte, e)
            if s > score_max:
                meilleur, score_max = nom, s
    return (meilleur, score_max) if score_max >= seuil else (None, score_max)


def dessiner(image: np.ndarray, boite: np.ndarray, texte: str, couleur: tuple[int, int, int]) -> None:
    x, y, w, h = [int(v) for v in boite[:4]]
    cv2.rectangle(image, (x, y), (x + w, y + h), couleur, 2)
    cv2.rectangle(image, (x, y - 24), (x + max(w, 12 * len(texte)), y), couleur, -1)
    cv2.putText(image, texte, (x + 4, y - 7), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
