"""
Envoi des alertes Telegram.

Lancé directement (python telegram_bot.py), ce fichier :
  - affiche le chat_id des personnes qui ont écrit au bot,
  - envoie un message de test si chat_id est rempli dans config.ini.
"""
from __future__ import annotations

import threading

import requests

from commun import charger_config


class Telegram:
    def __init__(self, token: str, chat_id: str):
        self.token, self.chat_id = token.strip(), chat_id.strip()
        self.actif = bool(self.token and self.chat_id)
        if not self.actif:
            print("[i] Telegram non configuré : les alertes s'afficheront seulement ici.")

    def _url(self, methode: str) -> str:
        return f"https://api.telegram.org/bot{self.token}/{methode}"

    def _envoyer(self, methode: str, data: dict, fichiers: dict | None = None) -> None:
        try:
            r = requests.post(self._url(methode), data=data, files=fichiers, timeout=15)
            if not r.ok:
                print(f"[x] Telegram : {r.status_code} {r.text[:120]}")
        except requests.RequestException as e:
            print(f"[x] Telegram injoignable : {e}")

    def message(self, texte: str) -> None:
        print(f"[Telegram] {texte}")
        if self.actif:  # dans un fil séparé pour ne pas figer la vidéo
            threading.Thread(target=self._envoyer, args=("sendMessage", {"chat_id": self.chat_id, "text": texte}), daemon=True).start()

    def photo(self, jpeg: bytes, legende: str) -> None:
        print(f"[Telegram] (photo) {legende}")
        if self.actif:
            threading.Thread(target=self._envoyer, daemon=True, args=(
                "sendPhoto", {"chat_id": self.chat_id, "caption": legende},
                {"photo": ("alerte.jpg", jpeg, "image/jpeg")})).start()


if __name__ == "__main__":
    cfg = charger_config()
    token = cfg.get("telegram", "token", fallback="").strip()
    chat_id = cfg.get("telegram", "chat_id", fallback="").strip()
    if not token:
        raise SystemExit("Mettez d'abord le token de @BotFather dans config.ini, section [telegram].")
    maj = requests.get(f"https://api.telegram.org/bot{token}/getUpdates", timeout=15).json()
    vus = {(u["message"]["chat"]["id"], u["message"]["chat"].get("first_name", "")) for u in maj.get("result", []) if "message" in u}
    if vus:
        for cid, nom in vus:
            print(f"chat_id de {nom} : {cid}")
    else:
        print("Aucun message reçu : envoyez « bonjour » à votre bot sur Telegram puis relancez.")
    if chat_id:
        Telegram(token, chat_id)._envoyer("sendMessage", {"chat_id": chat_id, "text": "Test : la maison intelligente est bien reliée à Telegram."})
        print("Message de test envoyé.")
