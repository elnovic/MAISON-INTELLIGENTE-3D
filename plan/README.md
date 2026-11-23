# Plan de la maison (source unique)

`plan.js` décrit **une seule fois** la maison :

- les pièces et leurs sols ;
- les murs, avec leurs portes, fenêtres et baies ;
- les 19 composants IoT : position, pièce, broche de l'ESP32 et rôle.

Ce fichier est utilisé à la fois par :

- le **jumeau 3D** (`jumeau-3d/index.html`), qui construit la maison et place les composants ;
- le **générateur de plans FabLab** :

```bash
python plan/generer_plans.py
```

| Fichier généré | Usage |
|---|---|
| `fabrication/plan_maison.svg` | Plan coté avec les composants numérotés |
| `fabrication/plan_cablage.svg` | Trajet des fils vers l'ESP32 et broche de chaque composant |
| `fabrication/murs_decoupe.svg` | Murs et plancher à découper au laser, à l'échelle 1/20 (MDF 3 mm). Rouge = découpe, bleu = gravure |

À l'échelle 1/20, la maison mesure **600 × 450 mm** et les murs **140 mm** de haut. Vérifiez que la découpeuse du FabLab accepte ce format ; sinon, coupez le plancher en deux.

## Maison retenue : plain-pied moderne à toit plat (12 × 9 m)

| Pièce | Composants |
|---|---|
| Séjour + cuisine | Radar LD2410, lampe, DHT22, ventilateur, chauffage, MQ-2 |
| Chambre | Radar LD2410, lampe |
| Entrée | Contact de porte ILS, écran OLED, bouton d'alarme |
| Façade | Caméra IA, sirène, photorésistance |
| Local technique | ESP32, relais, batterie + TP4056 + INA219 |
| Bureau | PC de vision (Python + OpenCV) |
| Terrasse | Pergola avec panneau solaire |

Pour modifier la maison, changez `plan.js`, puis relancez le générateur : la 3D et les plans restent toujours identiques.
