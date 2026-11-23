"""
Génère les plans de fabrication FabLab à partir de plan/plan.js,
le MÊME fichier que celui qu'utilise le jumeau 3D.

    python plan/generer_plans.py

Fichiers produits dans plan/fabrication/ :
  - plan_maison.svg      : plan coté avec les pièces et les objets connectés
  - plan_cablage.svg     : trajet des fils vers l'ESP32 + tableau des broches
  - murs_decoupe.svg     : pièces à découper au laser (échelle 1/20, MDF 3 mm)
                           rouge = découpe, bleu = gravure
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ICI = Path(__file__).resolve().parent
SORTIE = ICI / "fabrication"
texte = (ICI / "plan.js").read_text(encoding="utf-8")
PLAN = json.loads(re.sub(r"^\s*window\.PLAN\s*=\s*", "", texte).rstrip().rstrip(";"))

COULEURS = {"capteur": "#1f77b4", "actionneur": "#e8590c", "controleur": "#2b8a3e",
            "energie": "#c92a2a", "vision": "#7048e8"}
H = PLAN["hauteur_murs"]
ECH = PLAN["echelle_maquette"]


def svg(largeur_mm: float, hauteur_mm: float, contenu: str) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{largeur_mm}mm" height="{hauteur_mm}mm" '
            f'viewBox="0 0 {largeur_mm} {hauteur_mm}" font-family="Arial, sans-serif">\n{contenu}\n</svg>\n')


def plan_au_sol(avec_cablage: bool) -> str:
    """Plan vu de dessus, 1 m = 15 mm (échelle 1/66 sur A4 paysage)."""
    k, mx, my = 15.0, 20.0, 28.0
    X = lambda x: mx + x * k
    Y = lambda z: my + z * k
    s = []
    titre = "Plan de câblage" if avec_cablage else "Plan de la maison"
    s.append(f'<text x="{mx}" y="14" font-size="7" font-weight="bold">{titre} — {PLAN["nom"]}</text>')
    s.append(f'<text x="{mx}" y="21" font-size="3.6" fill="#555">Généré depuis plan/plan.js (même source que le jumeau 3D)</text>')
    for p in PLAN["pieces"]:
        s.append(f'<rect x="{X(p["x0"])}" y="{Y(p["z0"])}" width="{(p["x1"]-p["x0"])*k}" height="{(p["z1"]-p["z0"])*k}" fill="#f6f4ef" stroke="none"/>')
        s.append(f'<text x="{X((p["x0"]+p["x1"])/2)}" y="{Y((p["z0"]+p["z1"])/2)}" font-size="3.4" text-anchor="middle" fill="#666">{p["nom"]}</text>')
    for m in PLAN["murs"]:
        (x1, z1), (x2, z2) = m["de"], m["a"]
        ep = (PLAN["epaisseur_ext"] if m["ext"] else PLAN["epaisseur_int"]) * k
        horiz = z1 == z2
        L = (x2 - x1) if horiz else (z2 - z1)
        cur = 0.0
        segments = []
        for o in sorted(m["ouvertures"], key=lambda o: o["a"]):
            segments.append((cur, o["a"]))
            cur = o["b"]
            # ouverture : fenêtre = trait fin, porte = arc
            a, b = o["a"], o["b"]
            if o["type"] in ("fenetre", "baie"):
                if horiz:
                    s.append(f'<line x1="{X(x1+a)}" y1="{Y(z1)}" x2="{X(x1+b)}" y2="{Y(z1)}" stroke="#4dabf7" stroke-width="1.2"/>')
                else:
                    s.append(f'<line x1="{X(x1)}" y1="{Y(z1+a)}" x2="{X(x1)}" y2="{Y(z1+b)}" stroke="#4dabf7" stroke-width="1.2"/>')
        segments.append((cur, L))
        for a, b in segments:
            if b - a <= 0:
                continue
            if horiz:
                s.append(f'<rect x="{X(x1+a)}" y="{Y(z1)-ep/2}" width="{(b-a)*k}" height="{ep}" fill="#222"/>')
            else:
                s.append(f'<rect x="{X(x1)-ep/2}" y="{Y(z1+a)}" width="{ep}" height="{(b-a)*k}" fill="#222"/>')
    # terrasse (hors emprise) pour situer le panneau solaire
    W, D = PLAN["emprise"]
    s.append(f'<rect x="{X(-0.4)}" y="{Y(D+0.1)}" width="{7.6*k}" height="{3.0*k}" fill="none" stroke="#999" stroke-dasharray="1.5,1" stroke-width="0.3"/>')
    s.append(f'<text x="{X(3.4)}" y="{Y(D+2.9)}" font-size="3" text-anchor="middle" fill="#888">Terrasse (pergola solaire)</text>')
    # cotes
    s.append(f'<line x1="{X(0)}" y1="{Y(D)+52}" x2="{X(W)}" y2="{Y(D)+52}" stroke="#000" stroke-width="0.3"/>')
    s.append(f'<text x="{X(W/2)}" y="{Y(D)+56}" font-size="3.4" text-anchor="middle">{W} m (maquette : {W*1000/ECH:.0f} mm)</text>')
    s.append(f'<line x1="{X(W)+8}" y1="{Y(0)}" x2="{X(W)+8}" y2="{Y(D)}" stroke="#000" stroke-width="0.3"/>')
    s.append(f'<text x="{X(W)+11}" y="{Y(D/2)}" font-size="3.4" transform="rotate(90 {X(W)+11} {Y(D/2)})" text-anchor="middle">{D} m ({D*1000/ECH:.0f} mm)</text>')

    esp = next(o for o in PLAN["objets"] if o["id"] == "esp32")
    ex, ez = esp["pos"][0], esp["pos"][2]
    for i, o in enumerate(PLAN["objets"]):
        x, z = o["pos"][0], o["pos"][2]
        c = COULEURS[o["categorie"]]
        if avec_cablage and o["id"] == "panneau_solaire":
            b = next(q for q in PLAN["objets"] if q["id"] == "batterie")["pos"]
            s.append(f'<polyline points="{X(x)},{Y(z)} {X(b[0])},{Y(z)} {X(b[0])},{Y(b[2])}" fill="none" stroke="{c}" stroke-width="0.6" stroke-dasharray="2,1"/>')
        if avec_cablage and o["id"] not in ("esp32", "pc_vision", "camera", "panneau_solaire"):
            s.append(f'<polyline points="{X(x)},{Y(z)} {X(x)},{Y(ez)} {X(ex)},{Y(ez)}" fill="none" stroke="{c}" stroke-width="0.6" stroke-dasharray="{"" if o["categorie"] != "energie" else "2,1"}"/>')
        s.append(f'<circle cx="{X(x)}" cy="{Y(z)}" r="2.2" fill="{c}"/>')
        s.append(f'<text x="{X(x)}" y="{Y(z)+0.9}" font-size="2.4" text-anchor="middle" fill="#fff" font-weight="bold">{i+1}</text>')
    if avec_cablage:
        pc = next(o for o in PLAN["objets"] if o["id"] == "pc_vision")
        cam = next(o for o in PLAN["objets"] if o["id"] == "camera")
        s.append(f'<line x1="{X(cam["pos"][0])}" y1="{Y(cam["pos"][2])}" x2="{X(pc["pos"][0])}" y2="{Y(pc["pos"][2])}" stroke="#7048e8" stroke-width="0.6"/>')
        s.append(f'<line x1="{X(pc["pos"][0])}" y1="{Y(pc["pos"][2])}" x2="{X(ex)}" y2="{Y(ez)}" stroke="#7048e8" stroke-width="0.5" stroke-dasharray="1,1.5"/>')
    # légende
    lx, ly = X(W) + 22, my
    for i, o in enumerate(PLAN["objets"]):
        info = f'{o["nom"]} — {o["broche"]}' if avec_cablage and o["broche"] != "—" else o["nom"]
        s.append(f'<circle cx="{lx}" cy="{ly + i*7.2 - 1}" r="2" fill="{COULEURS[o["categorie"]]}"/>')
        s.append(f'<text x="{lx}" y="{ly + i*7.2 - 0.1}" font-size="2.2" text-anchor="middle" fill="#fff">{i+1}</text>')
        s.append(f'<text x="{lx+4}" y="{ly + i*7.2}" font-size="3">{info}</text>')
    if avec_cablage:
        s.append(f'<text x="{mx}" y="{Y(D)+64}" font-size="3.2">Trait plein : fil vers l\'ESP32 · pointillé rouge : alimentation · pointillé violet : WiFi/MQTT (PC vision ↔ ESP32)</text>')
    return svg(297, 250, "\n".join(s))


def murs_decoupe() -> str:
    """Chaque mur devient une pièce rectangulaire avec ses ouvertures (échelle 1/20, mm)."""
    f = 1000 / ECH
    s, x, y, ligne_h, largeur_max = [], 10.0, 18.0, 0.0, 580.0
    s.append(f'<text x="10" y="10" font-size="6" fill="blue">Murs à découper — échelle 1/{ECH} — MDF 3 mm — rouge : découpe, bleu : gravure</text>')
    for m in PLAN["murs"]:
        (x1, z1), (x2, z2) = m["de"], m["a"]
        L = abs((x2 - x1) if z1 == z2 else (z2 - z1)) * f
        h = H * f
        if x + L > largeur_max:
            x, y, ligne_h = 10.0, y + ligne_h + 12, 0.0
        s.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{L:.1f}" height="{h:.1f}" fill="none" stroke="red" stroke-width="0.1"/>')
        for o in m["ouvertures"]:
            ox, ow = x + o["a"] * f, (o["b"] - o["a"]) * f
            oy, oh = y + h - o["y1"] * f, (o["y1"] - o["y0"]) * f
            if o["y0"] == 0:   # ouverture jusqu'au sol : découpe en U
                s.append(f'<path d="M{ox:.1f},{y+h:.1f} V{oy:.1f} H{ox+ow:.1f} V{y+h:.1f}" fill="none" stroke="red" stroke-width="0.1"/>')
            else:
                s.append(f'<rect x="{ox:.1f}" y="{oy:.1f}" width="{ow:.1f}" height="{oh:.1f}" fill="none" stroke="red" stroke-width="0.1"/>')
        s.append(f'<text x="{x+3:.1f}" y="{y+7:.1f}" font-size="4" fill="blue">{m["id"]} {"ext." if m["ext"] else "int."}</text>')
        x += L + 8
        ligne_h = max(ligne_h, h)
    # plancher
    W, D = PLAN["emprise"]
    y += ligne_h + 14
    s.append(f'<rect x="10" y="{y:.1f}" width="{W*f:.1f}" height="{D*f:.1f}" fill="none" stroke="red" stroke-width="0.1"/>')
    s.append(f'<text x="14" y="{y+8:.1f}" font-size="4" fill="blue">Plancher {W*f:.0f} × {D*f:.0f} mm (graver le tracé des murs)</text>')
    for m in PLAN["murs"]:
        (x1, z1), (x2, z2) = m["de"], m["a"]
        s.append(f'<line x1="{10+x1*f:.1f}" y1="{y+z1*f:.1f}" x2="{10+x2*f:.1f}" y2="{y+z2*f:.1f}" stroke="blue" stroke-width="0.3"/>')
    for o in PLAN["objets"]:
        s.append(f'<circle cx="{10+o["pos"][0]*f:.1f}" cy="{y+o["pos"][2]*f:.1f}" r="1.5" fill="none" stroke="blue" stroke-width="0.3"/>')
    return svg(640, y + D * f + 15, "\n".join(s))


if __name__ == "__main__":
    SORTIE.mkdir(exist_ok=True)
    (SORTIE / "plan_maison.svg").write_text(plan_au_sol(False), encoding="utf-8")
    (SORTIE / "plan_cablage.svg").write_text(plan_au_sol(True), encoding="utf-8")
    (SORTIE / "murs_decoupe.svg").write_text(murs_decoupe(), encoding="utf-8")
    print(f"[ok] {len(PLAN['murs'])} murs, {len(PLAN['pieces'])} pièces, {len(PLAN['objets'])} objets connectés")
    print(f"[ok] Fichiers générés dans {SORTIE}")
