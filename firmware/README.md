# Firmware ESP32 + simulation Wokwi

## Lancer la simulation (navigateur, gratuit)

1. Allez sur <https://wokwi.com> → **New Project** → **ESP32**.
2. Remplacez le contenu de `sketch.ino` par celui de [`maison_intelligente/maison_intelligente.ino`](maison_intelligente/maison_intelligente.ino).
3. Remplacez `diagram.json` par [`maison_intelligente/diagram.json`](maison_intelligente/diagram.json). Tout le circuit apparaît.
4. Ajoutez un fichier `config.h` (bouton ▾ → *New file*) avec le contenu de [`config.h`](maison_intelligente/config.h).
5. Ajoutez un fichier `libraries.txt` avec le contenu de [`libraries.txt`](maison_intelligente/libraries.txt).
6. Cliquez sur ▶. Le moniteur série affiche les évènements, l'écran OLED l'état de la maison.

### Relier Wokwi au jumeau 3D (présentation)

1. Laissez la simulation Wokwi tourner (le moniteur série affiche « MQTT connecté »).
2. Ouvrez le jumeau 3D et choisissez **Simulation · firmware ESP32**.
3. Le jumeau envoie `cmd/source = jumeau` : le firmware lit alors les **capteurs virtuels** de la 3D (personnes, heure, température, porte, gaz, soleil). L'écran OLED de Wokwi affiche `[3D]`.
4. Faites entrer Marie dans le séjour : la LED jaune s'allume **dans Wokwi** et la lampe s'allume **dans la 3D**. C'est le même code qui décide.

Pour revenir aux capteurs de Wokwi, choisissez *Miroir de la maquette* (le jumeau envoie `cmd/source = materiel`).

### Ce que vous pouvez tester

| Action dans Wokwi | Réaction attendue |
|---|---|
| Cliquer sur le capteur **pres_salon** (PIR = radar) | Si la LDR indique « sombre », la LED jaune du séjour s'allume, puis s'éteint 10 s après la fin de la présence |
| Régler la LDR (lux élevés) | La lumière ne s'allume plus : il fait jour |
| Régler le DHT22 à 29 °C avec une présence | Le relais colle et la LED bleue (ventilateur) s'allume ; à 21 °C, c'est la LED rouge (chauffage) |
| Appuyer sur le bouton rouge | Alarme armée (LED orange). Après 15 s, ouvrir la porte (interrupteur) déclenche la vérification puis la sirène |
| Tourner **pot_gaz** au maximum | Alarme gaz, même désarmée |
| Baisser **pot_batterie** sous 20 % | Mode éco : la climatisation est coupée |

Pour simuler la caméra sans Python, publiez `{"resultat":"inconnu"}` sur `maison-ia/maison-ia-elnovic/vision` avec un client MQTT (MQTT Explorer, par exemple).

## Câblage

| Composant | Broche ESP32 | Remarque |
|---|---|---|
| Radar LD2410 séjour (OUT) | GPIO 27 | PIR dans Wokwi |
| Radar LD2410 chambre (OUT) | GPIO 26 | PIR dans Wokwi |
| DHT22 (DATA) | GPIO 15 | |
| LDR (AO) | GPIO 34 | ADC1 |
| MQ-2 (AO) | GPIO 35 | potentiomètre dans Wokwi |
| Panneau solaire (mesure) | GPIO 32 | potentiomètre ; INA219 en I2C en vrai |
| Batterie (mesure) | GPIO 33 | potentiomètre ; pont diviseur en vrai |
| Contact de porte ILS | GPIO 13 → GND | pull-up interne |
| Bouton alarme | GPIO 14 → GND | pull-up interne |
| Lumière séjour / chambre | GPIO 19 / 18 | LED + 220 Ω |
| Relais ventilateur | GPIO 23 | |
| LED chauffage | GPIO 5 | |
| Voyant armée / gyrophare | GPIO 4 / 16 | |
| Sirène (buzzer) | GPIO 25 | |
| OLED SSD1306 | SDA 21, SCL 22 | |

> Les entrées analogiques sont sur l'ADC1 (GPIO 32 à 39), car l'ADC2 ne fonctionne pas quand le WiFi est actif.

## Sur la vraie carte (FabLab)

1. Arduino IDE → installez le support **ESP32** (Espressif) et les 4 bibliothèques de `libraries.txt`.
2. Copiez `secrets.exemple.h` en `secrets.h` et mettez-y le WiFi du FabLab (`WIFI_CANAL 0`).
3. Ouvrez `maison_intelligente/maison_intelligente.ino` et téléversez.
4. Le radar LD2410 se branche **à l'identique** du PIR (sortie OUT). Alimentez-le en 5 V : sa sortie OUT est en 3,3 V, compatible ESP32.
5. Ventilateur : relais 5 V ou transistor (MOSFET logique). Ne passez jamais de 230 V dans la maquette.

Les réglages (seuils, délais, consigne) se trouvent tous dans [`config.h`](maison_intelligente/config.h).
