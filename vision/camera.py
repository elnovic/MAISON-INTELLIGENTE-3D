"""
Accès robuste à la caméra physique.

Sources acceptées (paramètre `source` de config.ini ou --source) :
  auto                          → première webcam qui fonctionne
  0, 1, 2…                      → webcam USB ou caméra intégrée
  http://192.168.1.50:81/stream → ESP32-CAM (firmware/esp32cam_flux)
  http://192.168.1.20:8080/video→ téléphone avec l'appli « IP Webcam » (Android)
  rtsp://utilisateur:mdp@ip/... → caméra de surveillance IP
  video.mp4                     → fichier vidéo (tests)

Points importants :
  - Sous Windows, on essaie DirectShow puis Media Foundation : selon le PC,
    l'un des deux ouvre la webcam beaucoup plus vite que l'autre.
  - Les images sont lues en continu dans un fil séparé : on analyse toujours
    l'image la plus récente, sans retard qui s'accumule.
  - En cas de coupure (câble USB, WiFi de l'ESP32-CAM), la caméra est
    rouverte automatiquement.
"""
from __future__ import annotations

import os
import platform
import threading
import time

import cv2
import numpy as np

SYSTEME = platform.system()


def backends_locaux() -> list[int]:
    if SYSTEME == "Windows":
        return [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]
    if SYSTEME == "Darwin":
        return [cv2.CAP_AVFOUNDATION, cv2.CAP_ANY]
    return [cv2.CAP_V4L2, cv2.CAP_ANY]


NOM_BACKEND = {cv2.CAP_ANY: "auto", cv2.CAP_DSHOW: "DirectShow", cv2.CAP_MSMF: "Media Foundation",
               cv2.CAP_V4L2: "V4L2", cv2.CAP_AVFOUNDATION: "AVFoundation", cv2.CAP_FFMPEG: "FFmpeg"}


def essayer_index(index: int, largeur: int, hauteur: int, delai: float = 4.0) -> tuple[cv2.VideoCapture | None, int | None]:
    """Ouvre une webcam locale en testant les pilotes ; renvoie (capture, pilote) ou (None, None)."""
    for backend in backends_locaux():
        cap = cv2.VideoCapture(index, backend)
        if not cap.isOpened():
            cap.release()
            continue
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, largeur)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, hauteur)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        fin = time.time() + delai
        while time.time() < fin:
            ok, image = cap.read()
            if ok and image is not None and image.size:
                return cap, backend
            time.sleep(0.05)
        cap.release()
    return None, None


def ouvrir_flux(url: str) -> cv2.VideoCapture | None:
    if url.lower().startswith("rtsp"):
        os.environ.setdefault("OPENCV_FFMPEG_CAPTURE_OPTIONS", "rtsp_transport;tcp")
    cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
    if not cap.isOpened():
        cap.release()
        cap = cv2.VideoCapture(url)
    if not cap.isOpened():
        cap.release()
        return None
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    return cap


class Camera:
    def __init__(self, source: str | int = "auto", largeur: int = 640, hauteur: int = 480,
                 rotation: int = 0, miroir: bool = False):
        self.source = str(source).strip()
        self.largeur, self.hauteur = largeur, hauteur
        self.rotation, self.miroir = rotation % 360, miroir
        self.est_fichier = os.path.isfile(self.source)
        self.description = ""
        self._cap: cv2.VideoCapture | None = None
        self._image: np.ndarray | None = None
        self._numero = 0
        self._numero_lu = -1
        self._verrou = threading.Lock()
        self._actif = False
        self._fin = False
        self._ouvrir(premiere_fois=True)
        if not self.est_fichier:
            self._actif = True
            threading.Thread(target=self._boucle, daemon=True).start()

    # ------------------------------------------------------------------
    def _ouvrir(self, premiere_fois: bool = False) -> bool:
        if self._cap is not None:
            self._cap.release()
            self._cap = None
        s = self.source
        if s.lower() == "auto":
            for i in range(6):
                cap, backend = essayer_index(i, self.largeur, self.hauteur, delai=2.5)
                if cap:
                    self._cap, self.description = cap, f"webcam n°{i} ({NOM_BACKEND.get(backend, backend)})"
                    break
        elif s.isdigit():
            cap, backend = essayer_index(int(s), self.largeur, self.hauteur)
            if cap:
                self._cap, self.description = cap, f"webcam n°{s} ({NOM_BACKEND.get(backend, backend)})"
        elif self.est_fichier:
            cap = cv2.VideoCapture(s)
            if cap.isOpened():
                self._cap, self.description = cap, f"fichier {os.path.basename(s)}"
        else:
            cap = ouvrir_flux(s)
            if cap:
                self._cap, self.description = cap, f"flux réseau {s}"
        if self._cap is None:
            if premiere_fois:
                conseil = ("Lancez « python lister_cameras.py » pour trouver le bon numéro de webcam."
                           if not s.startswith(("http", "rtsp")) else
                           "Vérifiez l'adresse dans un navigateur et que le PC est sur le même WiFi que la caméra.")
                raise SystemExit(f"[x] Impossible d'ouvrir la caméra « {s} ». {conseil}")
            return False
        w = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"[ok] Caméra : {self.description} — {w}×{h}")
        return True

    def _transformer(self, image: np.ndarray) -> np.ndarray:
        if self.rotation == 90:
            image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
        elif self.rotation == 180:
            image = cv2.rotate(image, cv2.ROTATE_180)
        elif self.rotation == 270:
            image = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
        if self.miroir:
            image = cv2.flip(image, 1)
        return image

    def _boucle(self) -> None:
        """Lecture continue (sources en direct) avec reconnexion automatique."""
        echecs, attente = 0, 1.0
        while self._actif:
            cap = self._cap
            ok, image = (cap.read() if cap is not None else (False, None))
            if ok and image is not None:
                echecs, attente = 0, 1.0
                with self._verrou:
                    self._image = self._transformer(image)
                    self._numero += 1
                continue
            echecs += 1
            if echecs >= 10:
                print(f"[!] Caméra perdue, nouvelle tentative dans {attente:.0f} s…")
                time.sleep(attente)
                attente = min(attente * 2, 15)
                if self._ouvrir():
                    echecs = 0
            else:
                time.sleep(0.05)

    # ------------------------------------------------------------------
    def lire(self, delai: float = 5.0) -> np.ndarray | None:
        """Renvoie la dernière image (copie). None si fin de fichier ou caméra muette."""
        if self.est_fichier:
            ok, image = self._cap.read() if self._cap else (False, None)
            return self._transformer(image) if ok else None
        fin = time.time() + delai
        dernier = self._numero_lu
        while time.time() < fin:
            with self._verrou:
                if self._image is not None and self._numero != dernier:
                    self._numero_lu = self._numero
                    return self._image.copy()
            time.sleep(0.005)
        with self._verrou:  # pas de nouvelle image : on renvoie la dernière connue
            return None if self._image is None else self._image.copy()

    def fermer(self) -> None:
        self._actif = False
        time.sleep(0.1)
        if self._cap is not None:
            self._cap.release()


def depuis_config(cfg, source: str | None = None) -> Camera:
    return Camera(
        source or cfg.get("camera", "source", fallback="auto"),
        cfg.getint("camera", "largeur", fallback=640),
        cfg.getint("camera", "hauteur", fallback=480),
        cfg.getint("camera", "rotation", fallback=0),
        cfg.getboolean("camera", "miroir", fallback=False),
    )
