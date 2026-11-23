window.PLAN = {
  "nom": "Maison moderne de plain-pied à toit plat",
  "unite": "m",
  "echelle_maquette": 20,
  "hauteur_murs": 2.8,
  "epaisseur_ext": 0.2,
  "epaisseur_int": 0.1,
  "emprise": [12, 9],

  "pieces": [
    {"id": "sejour",    "nom": "Séjour + cuisine", "x0": 0,   "z0": 3.5, "x1": 7,   "z1": 9,   "sol": "parquet"},
    {"id": "chambre",   "nom": "Chambre",          "x0": 0,   "z0": 0,   "x1": 5,   "z1": 3.5, "sol": "parquet"},
    {"id": "sdb",       "nom": "Salle de bain",    "x0": 5,   "z0": 0,   "x1": 8,   "z1": 3.5, "sol": "carrelage"},
    {"id": "bureau",    "nom": "Bureau (PC vision)","x0": 8,  "z0": 0,   "x1": 12,  "z1": 3.5, "sol": "parquet"},
    {"id": "couloir",   "nom": "Couloir",          "x0": 7,   "z0": 3.5, "x1": 12,  "z1": 5,   "sol": "carrelage"},
    {"id": "entree",    "nom": "Entrée",           "x0": 7,   "z0": 5,   "x1": 9.5, "z1": 9,   "sol": "carrelage"},
    {"id": "technique", "nom": "Local technique",  "x0": 9.5, "z0": 5,   "x1": 12,  "z1": 9,   "sol": "beton"}
  ],

  "murs": [
    {"id": "S1", "de": [0, 9],    "a": [7, 9],    "ext": true, "ouvertures": [{"a": 0.5, "b": 6.5, "y0": 0, "y1": 2.5, "type": "baie"}]},
    {"id": "S2", "de": [7, 9],    "a": [9.5, 9],  "ext": true, "ouvertures": [{"a": 0.75, "b": 1.75, "y0": 0, "y1": 2.2, "type": "porte_entree"}]},
    {"id": "S3", "de": [9.5, 9],  "a": [12, 9],   "ext": true, "bardage": true, "ouvertures": [{"a": 0.6, "b": 1.9, "y0": 0.9, "y1": 2.1, "type": "fenetre"}]},
    {"id": "N",  "de": [0, 0],    "a": [12, 0],   "ext": true, "ouvertures": [{"a": 1.5, "b": 3.5, "y0": 0.9, "y1": 2.2, "type": "fenetre"}, {"a": 6, "b": 7, "y0": 1.4, "y1": 2.1, "type": "fenetre"}, {"a": 9, "b": 11, "y0": 0.9, "y1": 2.2, "type": "fenetre"}]},
    {"id": "O",  "de": [0, 0],    "a": [0, 9],    "ext": true, "ouvertures": [{"a": 1, "b": 2.5, "y0": 0.9, "y1": 2.2, "type": "fenetre"}, {"a": 5.5, "b": 8.5, "y0": 0, "y1": 2.5, "type": "baie"}]},
    {"id": "E",  "de": [12, 0],   "a": [12, 9],   "ext": true, "bardage": true, "ouvertures": [{"a": 1, "b": 2.5, "y0": 0.9, "y1": 2.2, "type": "fenetre"}]},
    {"id": "I1", "de": [0, 3.5],  "a": [12, 3.5], "ext": false, "ouvertures": [{"a": 3.8, "b": 4.6, "y0": 0, "y1": 2.1, "type": "porte"}, {"a": 6, "b": 6.8, "y0": 0, "y1": 2.1, "type": "porte"}, {"a": 8.6, "b": 9.4, "y0": 0, "y1": 2.1, "type": "porte"}]},
    {"id": "I2", "de": [5, 0],    "a": [5, 3.5],  "ext": false, "ouvertures": []},
    {"id": "I3", "de": [8, 0],    "a": [8, 3.5],  "ext": false, "ouvertures": []},
    {"id": "I4", "de": [7, 3.5],  "a": [7, 9],    "ext": false, "ouvertures": [{"a": 0.1, "b": 1.4, "y0": 0, "y1": 2.1, "type": "passage"}, {"a": 1.9, "b": 2.9, "y0": 0, "y1": 2.1, "type": "porte"}]},
    {"id": "I5", "de": [7, 5],    "a": [12, 5],   "ext": false, "ouvertures": [{"a": 0.5, "b": 1.9, "y0": 0, "y1": 2.1, "type": "passage"}, {"a": 3.2, "b": 4.0, "y0": 0, "y1": 2.1, "type": "porte"}]},
    {"id": "I6", "de": [9.5, 5],  "a": [9.5, 9],  "ext": false, "ouvertures": []}
  ],

  "objets": [
    {"id": "esp32",          "type": "esp32",     "categorie": "controleur", "nom": "ESP32 DevKit",              "piece": "technique", "pos": [9.56, 1.5, 7.0],   "rot": 90,  "broche": "—",            "role": "Cerveau : lit les capteurs, décide, pilote les actionneurs, communique en MQTT"},
    {"id": "radar_salon",    "type": "ld2410",    "categorie": "capteur",    "nom": "Radar mmWave HLK-LD2410",   "piece": "sejour",    "pos": [2.6, 2.45, 3.56],  "rot": 0,   "broche": "GPIO 27",      "role": "Détecte la présence, même immobile", "mesure": "pres.salon"},
    {"id": "radar_chambre",  "type": "ld2410",    "categorie": "capteur",    "nom": "Radar mmWave HLK-LD2410",   "piece": "chambre",   "pos": [0.11, 2.45, 2.9],  "rot": 90,  "broche": "GPIO 26",      "role": "Détecte la présence dans la chambre", "mesure": "pres.chambre"},
    {"id": "ldr",            "type": "ldr",       "categorie": "capteur",    "nom": "Photorésistance (LDR)",     "piece": "exterieur", "pos": [11.6, 2.2, 9.11],  "rot": 0,   "broche": "GPIO 34 (ADC)", "role": "Mesure la lumière du jour : pas de lampe allumée en plein jour", "mesure": "lum"},
    {"id": "dht22",          "type": "dht22",     "categorie": "capteur",    "nom": "Capteur DHT22",             "piece": "sejour",    "pos": [6.94, 1.5, 6.9],   "rot": -90, "broche": "GPIO 15",      "role": "Température et humidité du séjour", "mesure": "t"},
    {"id": "mq2",            "type": "mq2",       "categorie": "capteur",    "nom": "Capteur de gaz MQ-2",       "piece": "sejour",    "pos": [1.2, 2.76, 4.1],   "rot": 0,   "broche": "GPIO 35 (ADC)", "role": "Fuite de gaz ou fumée dans la cuisine", "mesure": "gaz"},
    {"id": "ils_porte",      "type": "ils",       "categorie": "capteur",    "nom": "Contact magnétique ILS",    "piece": "entree",    "pos": [8.72, 2.0, 8.86],  "rot": 0,   "broche": "GPIO 13",      "role": "Détecte l'ouverture de la porte d'entrée", "mesure": "porte"},
    {"id": "camera",         "type": "camera",    "categorie": "vision",     "nom": "Caméra IA (vision par ordinateur)", "piece": "exterieur", "pos": [8.25, 2.5, 9.12], "rot": 0, "broche": "USB → PC",  "role": "Filme l'entrée ; Python + OpenCV reconnaît les résidents", "mesure": "vision"},
    {"id": "pc_vision",      "type": "pc",        "categorie": "vision",     "nom": "PC vision (Python + OpenCV)", "piece": "bureau",  "pos": [10.0, 0.78, 0.45], "rot": 0,   "broche": "WiFi / MQTT",  "role": "Analyse les images en temps réel et envoie « connu » / « inconnu » à l'ESP32"},
    {"id": "lampe_salon",    "type": "lampe",     "categorie": "actionneur", "nom": "Éclairage séjour (LED)",    "piece": "sejour",    "pos": [3.4, 2.76, 6.2],   "rot": 0,   "broche": "GPIO 19",      "role": "Lumière automatique du séjour", "mesure": "lumiere.salon"},
    {"id": "lampe_chambre",  "type": "lampe",     "categorie": "actionneur", "nom": "Éclairage chambre (LED)",   "piece": "chambre",   "pos": [2.5, 2.76, 1.9],   "rot": 0,   "broche": "GPIO 18",      "role": "Lumière automatique de la chambre", "mesure": "lumiere.chambre"},
    {"id": "ventilateur",    "type": "ventilateur","categorie": "actionneur","nom": "Ventilateur (via relais)",  "piece": "sejour",    "pos": [5.2, 2.45, 7.8],   "rot": 0,   "broche": "GPIO 23",      "role": "Rafraîchit le séjour quand il fait trop chaud", "mesure": "clim.ventilo"},
    {"id": "chauffage",      "type": "chauffage", "categorie": "actionneur", "nom": "Chauffage (LED rouge)",     "piece": "sejour",    "pos": [0.14, 0.55, 4.5],  "rot": 90,  "broche": "GPIO 5",       "role": "Réchauffe le séjour quand il fait trop froid", "mesure": "clim.chauffage"},
    {"id": "relais",         "type": "relais",    "categorie": "actionneur", "nom": "Module relais 5 V",         "piece": "technique", "pos": [9.56, 1.05, 7.55], "rot": 90,  "broche": "GPIO 23",      "role": "Commute l'alimentation du ventilateur", "mesure": "clim.ventilo"},
    {"id": "sirene",         "type": "sirene",    "categorie": "actionneur", "nom": "Sirène + gyrophare",        "piece": "exterieur", "pos": [9.9, 2.5, 9.12],   "rot": 0,   "broche": "GPIO 25 / 16", "role": "Alarme sonore et lumineuse", "mesure": "alarme"},
    {"id": "oled",           "type": "oled",      "categorie": "actionneur", "nom": "Écran OLED SSD1306",        "piece": "entree",    "pos": [9.44, 1.55, 6.6],  "rot": -90, "broche": "I2C SDA 21 / SCL 22", "role": "Affiche l'état de la maison dans l'entrée"},
    {"id": "bouton",         "type": "bouton",    "categorie": "capteur",    "nom": "Bouton armer / désarmer",   "piece": "entree",    "pos": [9.44, 1.15, 6.6],  "rot": -90, "broche": "GPIO 14",      "role": "Arme ou désarme l'alarme sans téléphone", "mesure": "alarme"},
    {"id": "panneau_solaire","type": "solaire",   "categorie": "energie",    "nom": "Mini panneau solaire 6 V",  "piece": "exterieur", "pos": [3.4, 2.82, 10.6],  "rot": 0,   "broche": "→ régulateur", "role": "Produit l'énergie de la maquette, indépendante du réseau", "mesure": "energie.solaire_w"},
    {"id": "batterie",       "type": "batterie",  "categorie": "energie",    "nom": "Batterie 18650 + TP4056 + INA219", "piece": "technique", "pos": [11.5, 0.0, 6.2], "rot": 0, "broche": "GPIO 32 / 33", "role": "Stocke l'énergie solaire ; l'INA219 mesure production et consommation", "mesure": "energie.batterie"}
  ]
};
