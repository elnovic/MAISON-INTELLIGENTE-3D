// =====================================================================
//  config.h — Réglages de la maison intelligente
//  Modifiez ce fichier pour adapter le comportement sans toucher au code.
// =====================================================================
#pragma once

// Si un fichier secrets.h existe (non publié sur GitHub), il remplace
// les valeurs ci-dessous : mettez-y le vrai WiFi du FabLab.
#if __has_include("secrets.h")
#include "secrets.h"
#endif

// ---------------------------------------------------------------------
//  Identifiant de la maison : il doit être IDENTIQUE dans
//  - ce fichier,
//  - le jumeau numérique 3D (champ « ID maison »),
//  - vision/config.ini.
//  Le broker MQTT est public : choisissez un identifiant unique.
// ---------------------------------------------------------------------
#ifndef MAISON_ID
#define MAISON_ID "maison-ia-elnovic"
#endif

// --------------------------- WiFi ------------------------------------
// Dans Wokwi : réseau "Wokwi-GUEST", sans mot de passe, canal 6.
#ifndef WIFI_SSID
#define WIFI_SSID "Wokwi-GUEST"
#endif
#ifndef WIFI_MDP
#define WIFI_MDP ""
#endif
#ifndef WIFI_CANAL
#define WIFI_CANAL 6   // mettre 0 avec une vraie box (recherche automatique)
#endif

// --------------------------- MQTT ------------------------------------
#ifndef MQTT_HOTE
#define MQTT_HOTE "broker.hivemq.com"
#endif
#ifndef MQTT_PORT
#define MQTT_PORT 1883
#endif

// ------------------------- Éclairage ---------------------------------
#define SEUIL_NUIT          40     // % de luminosité en dessous duquel il fait "sombre"
#define HYST_LUMIERE        10     // marge pour éviter les clignotements
#define DELAI_EXTINCTION_MS 10000  // extinction après 10 s sans présence (démo ; 2 min en vrai)
#define INVERSER_LDR        true   // module LDR : tension haute = sombre (Wokwi et KY-018)

// ------------------------ Température --------------------------------
#define CONSIGNE_DEFAUT       24.0  // °C
#define HYST_CLIM             1.0   // ventilateur à consigne+1, arrêt à la consigne
#define DELAI_ABSENCE_CLIM_MS 60000 // coupe la clim 60 s après le départ de la personne

// ------------------------- Sécurité ----------------------------------
#define DELAI_ENTREE_MS 15000  // temps laissé à la caméra pour reconnaître un résident
#define DELAI_SORTIE_MS 15000  // temps pour sortir après avoir armé l'alarme
#define SEUIL_GAZ       60     // % du capteur MQ-2 déclenchant l'alarme gaz

// ------------------------- Énergie -----------------------------------
#define SOLAIRE_MAX_W 6.0      // puissance du mini panneau solaire
#define SEUIL_ECO     20       // % batterie : passage en mode économie

// Consommation de la maquette (pour le bilan énergétique)
#define CONSO_BASE_W      0.8   // ESP32 + capteurs
#define CONSO_LAMPE_W     0.5   // par lampe LED
#define CONSO_VENTILO_W   1.2
#define CONSO_CHAUFFAGE_W 2.0

// ------------------------- Source des capteurs -----------------------
// false : capteurs réels (Wokwi ou maquette FabLab)
// true  : capteurs virtuels envoyés par le jumeau 3D
// Le jumeau 3D change cette valeur à chaud (topic cmd/source).
#define SOURCE_JUMEAU_DEFAUT false

// ------------------------- Divers ------------------------------------
#define PERIODE_ETAT_MS 2000   // envoi de l'état au téléphone / jumeau 3D
