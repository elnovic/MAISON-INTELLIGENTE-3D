# Matériel pour la maquette FabLab

Les prix sont indicatifs (boutiques en ligne d'électronique) et varient selon le vendeur.

| Qté | Composant | Rôle | Prix indicatif |
|---|---|---|---|
| 1 | ESP32 DevKit (WROOM-32) | Cerveau de la maison | 6–10 € |
| 2 | Radar mmWave HLK-LD2410 (ou LD2410C) | Présence, même immobile | 4–8 € pièce |
| 1 | Module photorésistance (LDR) | Lumière du jour | 1–2 € |
| 1 | DHT22 (AM2302) | Température et humidité | 3–6 € |
| 1 | Module relais 5 V, 1 canal | Commande du ventilateur | 1–3 € |
| 1 | Ventilateur 5 V (40 ou 50 mm) | « Climatisation » | 2–4 € |
| 1 | Contact magnétique ILS (reed) de porte | Détection d'ouverture | 1–3 € |
| 1 | Capteur de gaz MQ-2 | Fuite de gaz, fumée | 2–4 € |
| 1 | Buzzer actif ou petite sirène 5 V | Alarme | 1–3 € |
| 1 | Écran OLED SSD1306 0,96" I2C | Affichage local | 3–5 € |
| 1 | Capteur de courant INA219 | Mesure solaire et consommation | 2–4 € |
| 1 | Mini panneau solaire 6 V, 1 à 6 W | Production d'énergie | 5–15 € |
| 1 | Batterie Li-ion 18650 + support (ou batterie LiFePO4) | Stockage | 5–10 € |
| 1 | Module de charge TP4056 avec protection (ou régulateur solaire) | Charge sûre de la batterie | 1–3 € |
| 1 | Convertisseur élévateur MT3608 (3,7 V → 5 V) | Alimentation 5 V | 1–2 € |
| 6 | LED (2 blanches ou jaunes, 2 rouges, 1 orange, 1 bleue) + résistances 220 Ω | Lumières et voyants | 2 € |
| 1 | Bouton poussoir | Armer / désarmer | < 1 € |
| — | Breadboard, fils Dupont, MDF 3 mm, plexiglas | Maquette | 10–20 € |
| 1 | Webcam USB (ou ESP32-CAM, 8–12 €) | Caméra IA reliée au PC | déjà disponible ? |

**Total estimé : environ 60 à 110 €** sans la webcam.

## Règles de sécurité

- Tout fonctionne en **5 V / 3,3 V**. Pas de 230 V dans la maquette.
- Ne branchez jamais le panneau directement sur la batterie : passez toujours par le module de charge.
- Le MQ-2 chauffe et doit préchauffer 1 à 2 minutes avant de donner des mesures fiables.
- Sa sortie analogique peut monter jusqu'à 5 V : utilisez un pont diviseur (10 kΩ / 20 kΩ) avant le GPIO 35.
