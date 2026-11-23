/*
 * =====================================================================
 *  MAISON INTELLIGENTE IoT — Firmware ESP32
 * =====================================================================
 *  Fonctions :
 *   1. Éclairage automatique   : radar de présence (HLK-LD2410) + LDR
 *   2. Température             : DHT22 → ventilateur (relais) / chauffage (LED rouge)
 *   3. Sécurité                : contact de porte (ILS) + caméra IA (via MQTT)
 *                                + capteur de gaz MQ-2 + sirène
 *   4. Énergie                 : suivi panneau solaire / batterie, mode éco
 *   5. Pilotage téléphone      : MQTT (jumeau numérique 3D, appli, Python)
 *
 *  UN SEUL CODE pour le virtuel et le réel :
 *   - source "materiel" : capteurs lus sur les broches (Wokwi ou maquette FabLab)
 *   - source "jumeau"   : capteurs virtuels envoyés par le jumeau 3D
 *                         (topic .../capteurs/virtuels). Le jumeau joue le
 *                         rôle du monde physique, ce firmware reste le cerveau.
 *   Changement à chaud par MQTT : .../cmd/source = jumeau | materiel
 *
 *  La maison reste 100 % fonctionnelle SANS WiFi : toutes les décisions
 *  sont prises localement par l'ESP32, le réseau sert seulement à
 *  informer et à recevoir des ordres.
 *
 *  Simulation Wokwi :
 *   - le radar LD2410 est remplacé par un capteur PIR (même sortie OUT
 *     numérique : HIGH = présence). Aucune ligne de code à changer.
 *   - le capteur de gaz, le panneau solaire et la batterie sont simulés
 *     par des potentiomètres.
 * =====================================================================
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <DHTesp.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include "config.h"

// ============================ BROCHES =================================
// Entrées
const int PIN_PRES_SALON   = 27;  // LD2410 (séjour)  — sortie OUT
const int PIN_PRES_CHAMBRE = 26;  // LD2410 (chambre) — sortie OUT
const int PIN_DHT          = 15;  // DHT22
const int PIN_LDR          = 34;  // photorésistance (sortie analogique AO)
const int PIN_GAZ          = 35;  // MQ-2 (sortie analogique)
const int PIN_SOLAIRE      = 32;  // mesure panneau solaire (INA219 plus tard)
const int PIN_BATTERIE     = 33;  // mesure tension batterie (pont diviseur)
const int PIN_PORTE        = 13;  // contact magnétique ILS (vers GND)
const int PIN_BOUTON       = 14;  // bouton armer / désarmer (vers GND)
// Sorties
const int PIN_LUM_SALON    = 19;
const int PIN_LUM_CHAMBRE  = 18;
const int PIN_VENTILO      = 23;  // relais du ventilateur
const int PIN_CHAUFFAGE    = 5;   // LED rouge "chauffage"
const int PIN_LED_ARMEE    = 4;   // voyant alarme armée
const int PIN_LED_ALARME   = 16;  // gyrophare
const int PIN_BUZZER       = 25;  // sirène
// Écran OLED I2C : SDA = 21, SCL = 22

// Les entrées analogiques utilisent l'ADC1 (GPIO 32 à 39) car l'ADC2
// ne fonctionne pas quand le WiFi est actif.

// ============================ TYPES ===================================
enum ModeLumiere { LUM_AUTO, LUM_ON, LUM_OFF };
enum EtatAlarme  { DESARMEE, ARMEE, VERIFICATION, DECLENCHEE };

const char* NOM_MODE_LUM[] = {"auto", "on", "off"};
const char* NOM_ALARME[]   = {"desarmee", "armee", "verification", "declenchee"};

struct Piece {
  const char* nom;
  int pinPresence;
  int pinLumiere;
  bool presence;            // présence détectée à l'instant
  bool occupee;             // présence récente (avec délai d'extinction)
  bool lumiere;             // état de la lampe
  ModeLumiere mode;
  bool dejaVue;
  unsigned long dernierePresence;
};

const int NB_PIECES = 2;
Piece pieces[NB_PIECES] = {
  {"salon",   PIN_PRES_SALON,   PIN_LUM_SALON,   false, false, false, LUM_AUTO, false, 0},
  {"chambre", PIN_PRES_CHAMBRE, PIN_LUM_CHAMBRE, false, false, false, LUM_AUTO, false, 0},
};

// ============================ ÉTAT ====================================
DHTesp dht;
Adafruit_SSD1306 ecran(128, 64, &Wire, -1);
bool ecranOk = false;
WiFiClient wifiClient;
PubSubClient mqtt(wifiClient);

float temperature = NAN;
float humidite    = NAN;
int   luminosite  = 0;     // %
int   gaz         = 0;     // %
float solaireW    = 0;
int   batterie    = 100;   // %
bool  modeEco     = false;

bool  climAuto    = true;
float consigne    = CONSIGNE_DEFAUT;
bool  ventilo     = false;
bool  chauffage   = false;

bool  porteLue     = false;   // dernière lecture du contact de porte
bool  porteOuverte = false;
EtatAlarme alarme  = DESARMEE;
String causeAlarme = "";
unsigned long debutVerification = 0;
unsigned long armeeDepuis       = 0;

bool boutonPrecedent = HIGH;
unsigned long dernierAppui = 0;

unsigned long dernierDHT = 0, dernierEtat = 0, dernierEcran = 0, dernierEssaiMQTT = 0;
bool etatModifie = true;

String base;   // "maison-ia/<MAISON_ID>"

// ---------- Capteurs virtuels (jumeau 3D) ----------
bool sourceJumeau = SOURCE_JUMEAU_DEFAUT;
struct CapteursVirtuels {
  bool presSalon = false, presChambre = false, porte = false;
  float t = NAN, h = NAN, solaire = 0;
  int lum = 50, gaz = 0, batterie = 100;
} virt;

// ---------- Bilan énergétique ----------
float consoW = 0;
double whConso = 0, whReference = 0;   // consommé / consommation qu'aurait eue une maison sans IA
unsigned long dernierBilan = 0;

// ============================ OUTILS ==================================
void journal(const String& m) {
  Serial.printf("[%8lu] %s\n", millis() / 1000, m.c_str());
}

int lirePourcent(int pin) {
  int v = (int)map(analogRead(pin), 0, 4095, 0, 100);
  return v < 0 ? 0 : (v > 100 ? 100 : v);
}

// Pilote la sirène sans rappeler tone() inutilement à chaque tour de boucle
unsigned int frequenceBuzzer = 0;
void buzzer(unsigned int f) {
  if (f == frequenceBuzzer) return;
  frequenceBuzzer = f;
  if (f == 0) noTone(PIN_BUZZER); else tone(PIN_BUZZER, f);
}

void publierEvenement(const char* type, const String& detail) {
  journal(String("Évènement : ") + type + " " + detail);
  if (!mqtt.connected()) return;
  String json = String("{\"type\":\"") + type + "\",\"detail\":\"" + detail + "\"}";
  mqtt.publish((base + "/evenement").c_str(), json.c_str());
}

// ============================ CAPTEURS ================================
void majPresences(unsigned long now, const bool* p) {
  for (int i = 0; i < NB_PIECES; i++) {
    if (p[i] != pieces[i].presence) etatModifie = true;
    pieces[i].presence = p[i];
    if (p[i]) { pieces[i].dernierePresence = now; pieces[i].dejaVue = true; }
    pieces[i].occupee = p[i] || (pieces[i].dejaVue && now - pieces[i].dernierePresence < DELAI_EXTINCTION_MS);
  }
}

// Lit une valeur numérique dans un petit JSON : {"t":24.5,"pres_salon":1}
bool extraire(const String& json, const char* cle, float& valeur) {
  String motif = String("\"") + cle + "\":";
  int i = json.indexOf(motif);
  if (i < 0) return false;
  valeur = json.substring(i + motif.length()).toFloat();
  return true;
}

void lireCapteurs(unsigned long now) {
  if (sourceJumeau) {
    // --- Monde virtuel : valeurs envoyées par le jumeau 3D ---
    if (!isnan(virt.t) && (isnan(temperature) || fabs(virt.t - temperature) >= 0.1)) etatModifie = true;
    temperature = virt.t;  humidite = virt.h;
    luminosite = virt.lum; gaz = virt.gaz;
    solaireW = virt.solaire; batterie = virt.batterie;
    porteLue = virt.porte;
    bool p[NB_PIECES] = {virt.presSalon, virt.presChambre};
    majPresences(now, p);
    return;
  }

  // --- Monde réel : broches de l'ESP32 (Wokwi ou maquette FabLab) ---
  // DHT22 : une lecture toutes les 2 s maximum
  if (now - dernierDHT >= 2000) {
    dernierDHT = now;
    TempAndHumidity d = dht.getTempAndHumidity();
    if (dht.getStatus() == 0) {
      if (isnan(temperature) || fabs(d.temperature - temperature) >= 0.1) etatModifie = true;
      temperature = d.temperature;
      humidite = d.humidity;
    }
  }

  int brut = lirePourcent(PIN_LDR);
  luminosite = INVERSER_LDR ? 100 - brut : brut;
  gaz = lirePourcent(PIN_GAZ);
  solaireW = SOLAIRE_MAX_W * lirePourcent(PIN_SOLAIRE) / 100.0;
  batterie = lirePourcent(PIN_BATTERIE);
  porteLue = digitalRead(PIN_PORTE) == HIGH;  // aimant éloigné = porte ouverte

  bool p[NB_PIECES];
  for (int i = 0; i < NB_PIECES; i++) p[i] = digitalRead(pieces[i].pinPresence) == HIGH;
  majPresences(now, p);
}

// ============================ ÉCLAIRAGE ===============================
void majEclairage() {
  for (int i = 0; i < NB_PIECES; i++) {
    bool voulu;
    if (pieces[i].mode == LUM_ON)       voulu = true;
    else if (pieces[i].mode == LUM_OFF) voulu = false;
    else {
      // allume s'il fait sombre ; reste allumée tant que la lumière
      // ne dépasse pas nettement le seuil (hystérésis)
      bool sombre = luminosite < SEUIL_NUIT ||
                    (pieces[i].lumiere && luminosite < SEUIL_NUIT + HYST_LUMIERE);
      voulu = pieces[i].occupee && sombre;
    }
    if (voulu != pieces[i].lumiere) {
      pieces[i].lumiere = voulu;
      etatModifie = true;
      journal(String("Lumière ") + pieces[i].nom + (voulu ? " ALLUMÉE" : " éteinte"));
    }
    digitalWrite(pieces[i].pinLumiere, voulu ? HIGH : LOW);
  }
}

// ============================ ÉNERGIE =================================
void majEnergie() {
  bool eco = modeEco ? batterie < SEUIL_ECO + 5 : batterie < SEUIL_ECO;
  if (eco != modeEco) {
    modeEco = eco;
    etatModifie = true;
    publierEvenement("energie", eco ? "mode eco active" : "mode eco desactive");
  }
}

// Bilan : consommation réelle comparée à une maison « sans IA »
// (lampes allumées dès qu'il fait sombre, clim selon la température seule)
void majBilanEnergie(unsigned long now) {
  if (dernierBilan == 0) { dernierBilan = now; return; }
  double heures = (now - dernierBilan) / 3600000.0;
  dernierBilan = now;
  int lampes = pieces[0].lumiere + pieces[1].lumiere;
  consoW = CONSO_BASE_W + CONSO_LAMPE_W * lampes + CONSO_VENTILO_W * ventilo + CONSO_CHAUFFAGE_W * chauffage;
  bool sombre = luminosite < SEUIL_NUIT;
  bool chaud = !isnan(temperature) && temperature >= consigne + HYST_CLIM;
  bool froid = !isnan(temperature) && temperature <= consigne - HYST_CLIM;
  float reference = CONSO_BASE_W + CONSO_LAMPE_W * NB_PIECES * sombre + CONSO_VENTILO_W * chaud + CONSO_CHAUFFAGE_W * froid;
  whConso += consoW * heures;
  whReference += reference * heures;
}

// ============================ TEMPÉRATURE =============================
void majClimatisation(unsigned long now) {
  bool v = ventilo, c = chauffage;
  // La clim ne fonctionne que si quelqu'un est (ou était récemment) dans le séjour
  bool presenceRecente = pieces[0].dejaVue && now - pieces[0].dernierePresence < DELAI_ABSENCE_CLIM_MS;

  if (!climAuto || modeEco || isnan(temperature) || !presenceRecente) {
    v = false;
    c = false;
  } else {
    if (temperature >= consigne + HYST_CLIM) v = true;
    else if (temperature <= consigne)        v = false;
    if (temperature <= consigne - HYST_CLIM) c = true;
    else if (temperature >= consigne)        c = false;
  }
  if (v != ventilo || c != chauffage) {
    ventilo = v; chauffage = c;
    etatModifie = true;
    journal(String("Clim : ventilateur ") + (v ? "ON" : "off") + ", chauffage " + (c ? "ON" : "off"));
  }
  digitalWrite(PIN_VENTILO, ventilo ? HIGH : LOW);
  digitalWrite(PIN_CHAUFFAGE, chauffage ? HIGH : LOW);
}

// ============================ ALARME ==================================
void changerAlarme(EtatAlarme e, const String& cause) {
  if (e == alarme && cause == causeAlarme) return;
  alarme = e;
  causeAlarme = cause;
  etatModifie = true;
  if (e == ARMEE) armeeDepuis = millis();
  if (e == VERIFICATION) debutVerification = millis();
  publierEvenement(NOM_ALARME[e], cause);
}

void armer()    { if (alarme == DESARMEE) changerAlarme(ARMEE, ""); }
void desarmer() { changerAlarme(DESARMEE, ""); }

void majAlarme(unsigned long now) {
  bool porte = porteLue;
  bool porteVientDOuvrir = porte && !porteOuverte;
  if (porte != porteOuverte) {
    porteOuverte = porte;
    etatModifie = true;
    journal(porte ? "Porte OUVERTE" : "Porte fermée");
  }

  // Le gaz déclenche l'alarme même quand elle est désarmée
  if (gaz >= SEUIL_GAZ && !(alarme == DECLENCHEE && causeAlarme == "gaz")) {
    changerAlarme(DECLENCHEE, "gaz");
  }

  bool presence = pieces[0].presence || pieces[1].presence;
  switch (alarme) {
    case ARMEE:
      if (now - armeeDepuis > DELAI_SORTIE_MS) {
        if (porteVientDOuvrir)  changerAlarme(VERIFICATION, "porte");
        else if (presence)      changerAlarme(VERIFICATION, "presence");
      }
      break;
    case VERIFICATION:
      // Personne n'a été reconnu à temps par la caméra
      if (now - debutVerification > DELAI_ENTREE_MS) changerAlarme(DECLENCHEE, causeAlarme);
      break;
    default:
      break;
  }
}

// Résultat envoyé par le programme Python de vision par ordinateur
void resultatVision(bool connu) {
  if (connu) {
    if (alarme == VERIFICATION || (alarme == DECLENCHEE && causeAlarme != "gaz") || alarme == ARMEE) {
      changerAlarme(DESARMEE, "");
      publierEvenement("bienvenue", "resident reconnu");
    }
  } else {
    if (alarme == ARMEE || alarme == VERIFICATION) changerAlarme(DECLENCHEE, "intrus");
    else if (alarme == DESARMEE) publierEvenement("visiteur", "visage inconnu");
  }
}

void majSortiesAlarme(unsigned long now) {
  bool clignoteRapide = (now / 125) % 2;
  bool clignoteLent   = (now / 500) % 2;

  digitalWrite(PIN_LED_ARMEE, alarme == ARMEE || (alarme == VERIFICATION && clignoteLent));
  digitalWrite(PIN_LED_ALARME, alarme == DECLENCHEE && clignoteRapide);

  unsigned int f = 0;
  if (alarme == DECLENCHEE)        f = ((now / 400) % 2) ? 1800 : 1200;  // sirène deux tons
  else if (alarme == VERIFICATION) f = ((now % 1000) < 80) ? 2500 : 0;   // bip de compte à rebours
  buzzer(f);
}

// Bouton de l'entrée : appui court = armer / désarmer ; appui long (3 s) = alarme panique
unsigned long debutAppui = 0;
bool paniqueEnvoyee = false;
void lireBouton(unsigned long now) {
  bool b = digitalRead(PIN_BOUTON);
  if (b == LOW && boutonPrecedent == HIGH) { debutAppui = now; paniqueEnvoyee = false; }
  if (b == LOW && !paniqueEnvoyee && now - debutAppui > 3000) {
    paniqueEnvoyee = true;
    changerAlarme(DECLENCHEE, "panique");
  }
  if (b == HIGH && boutonPrecedent == LOW && !paniqueEnvoyee && now - debutAppui > 40 && now - dernierAppui > 250) {
    dernierAppui = now;
    if (alarme == DESARMEE) armer(); else desarmer();
  }
  boutonPrecedent = b;
}

// ============================ MQTT ====================================
void recevoirMessage(char* topic, byte* charge, unsigned int longueur) {
  String t(topic);
  String msg;
  for (unsigned int i = 0; i < longueur; i++) msg += (char)charge[i];
  msg.trim();
  String m = msg;
  m.toLowerCase();
  if (t.indexOf("/capteurs/") < 0) journal("MQTT ← " + t + " : " + msg);

  ModeLumiere ml = (m == "on") ? LUM_ON : (m == "off") ? LUM_OFF : LUM_AUTO;
  if (t == base + "/cmd/lumiere/salon")        pieces[0].mode = ml;
  else if (t == base + "/cmd/lumiere/chambre") pieces[1].mode = ml;
  else if (t == base + "/cmd/clim")            climAuto = (m != "off");
  else if (t == base + "/cmd/consigne") {
    float c = msg.toFloat();
    if (c >= 16 && c <= 30) consigne = c;
  }
  else if (t == base + "/cmd/alarme") {
    if (m == "armer") armer();
    else if (m == "desarmer" || m == "stop") desarmer();
    else if (m == "panique") changerAlarme(DECLENCHEE, "panique");  // bouton SOS du site
  }
  else if (t == base + "/cmd/source") {
    sourceJumeau = (m == "jumeau");
    journal(String("Source des capteurs : ") + (sourceJumeau ? "JUMEAU 3D (virtuels)" : "MATÉRIEL (broches)"));
  }
  else if (t == base + "/capteurs/virtuels") {
    float v;
    if (extraire(msg, "pres_salon", v))   virt.presSalon = v > 0.5;
    if (extraire(msg, "pres_chambre", v)) virt.presChambre = v > 0.5;
    if (extraire(msg, "porte", v))        virt.porte = v > 0.5;
    if (extraire(msg, "t", v))            virt.t = v;
    if (extraire(msg, "h", v))            virt.h = v;
    if (extraire(msg, "lum", v))          virt.lum = (int)v;
    if (extraire(msg, "gaz", v))          virt.gaz = (int)v;
    if (extraire(msg, "solaire", v))      virt.solaire = v;
    if (extraire(msg, "batterie", v))     virt.batterie = (int)v;
    return;  // pas de journal : ce message arrive plusieurs fois par seconde
  }
  else if (t == base + "/vision") {
    // {"resultat":"connu","score":0.62}  — tester "inconnu" en premier !
    if (m.indexOf("inconnu") >= 0)    resultatVision(false);
    else if (m.indexOf("connu") >= 0) resultatVision(true);
  }
  etatModifie = true;
}

void publierEtat() {
  if (!mqtt.connected()) return;
  char t[10], h[10];
  if (isnan(temperature)) strcpy(t, "null"); else snprintf(t, sizeof(t), "%.1f", temperature);
  if (isnan(humidite))    strcpy(h, "null"); else snprintf(h, sizeof(h), "%.0f", humidite);

  char json[900];
  snprintf(json, sizeof(json),
    "{\"t\":%s,\"h\":%s,\"lum\":%d,\"gaz\":%d,"
    "\"pres\":{\"salon\":%d,\"chambre\":%d},"
    "\"lumiere\":{\"salon\":%d,\"chambre\":%d},"
    "\"mode_lum\":{\"salon\":\"%s\",\"chambre\":\"%s\"},"
    "\"clim\":{\"mode\":\"%s\",\"consigne\":%.1f,\"ventilo\":%d,\"chauffage\":%d},"
    "\"porte\":%d,\"alarme\":\"%s\",\"cause\":\"%s\","
    "\"energie\":{\"solaire_w\":%.1f,\"batterie\":%d,\"eco\":%d,"
    "\"conso_w\":%.2f,\"wh\":%.3f,\"wh_ref\":%.3f},"
    "\"source\":\"%s\",\"uptime\":%lu}",
    t, h, luminosite, gaz,
    pieces[0].presence, pieces[1].presence,
    pieces[0].lumiere, pieces[1].lumiere,
    NOM_MODE_LUM[pieces[0].mode], NOM_MODE_LUM[pieces[1].mode],
    climAuto ? "auto" : "off", consigne, ventilo, chauffage,
    porteOuverte, NOM_ALARME[alarme], causeAlarme.c_str(),
    solaireW, batterie, modeEco,
    consoW, whConso, whReference,
    sourceJumeau ? "jumeau" : "materiel", millis() / 1000);
  mqtt.publish((base + "/etat").c_str(), json, true);  // retenu : le téléphone reçoit l'état dès sa connexion
}

void gererReseau(unsigned long now) {
  if (WiFi.status() != WL_CONNECTED) return;  // la reconnexion WiFi est automatique
  if (mqtt.connected()) { mqtt.loop(); return; }
  if (now - dernierEssaiMQTT < 5000) return;
  dernierEssaiMQTT = now;

  String id = "esp32-" + String(MAISON_ID) + "-" + String((uint32_t)ESP.getEfuseMac(), HEX);
  String dispo = base + "/disponible";
  journal("Connexion MQTT à " MQTT_HOTE "…");
  if (mqtt.connect(id.c_str(), NULL, NULL, dispo.c_str(), 1, true, "offline")) {
    journal("MQTT connecté. Topic de base : " + base);
    mqtt.publish(dispo.c_str(), "online", true);
    mqtt.subscribe((base + "/cmd/#").c_str());
    mqtt.subscribe((base + "/vision").c_str());
    mqtt.subscribe((base + "/capteurs/virtuels").c_str());
    etatModifie = true;
  } else {
    journal("Échec MQTT (code " + String(mqtt.state()) + "), nouvel essai dans 5 s");
  }
}

// ============================ ÉCRAN ===================================
void majEcran() {
  if (!ecranOk) return;
  const char* txtAlarme[] = {"Desarmee", "ARMEE", "VERIF...", "!! ALARME !!"};
  ecran.clearDisplay();
  ecran.setTextSize(1);
  ecran.setTextColor(SSD1306_WHITE);
  ecran.setCursor(0, 0);
  ecran.printf("%s %s %s\n", WiFi.status() == WL_CONNECTED ? "WiFi" : "----",
                          mqtt.connected() ? "MQTT" : "----", sourceJumeau ? "[3D]" : "[REEL]");
  if (isnan(temperature)) ecran.print("T: --.- C");
  else ecran.printf("T:%.1fC  H:%.0f%%", temperature, humidite);
  ecran.printf("\nLum:%d%%  Gaz:%d%%\n", luminosite, gaz);
  ecran.printf("Clim:%s %s\n", ventilo ? "VENTILO" : chauffage ? "CHAUFFE" : "repos",
                              climAuto ? "" : "(off)");
  ecran.printf("Sol:%.1fW Bat:%d%%%s\n", solaireW, batterie, modeEco ? " ECO" : "");
  ecran.printf("Porte:%s\n", porteOuverte ? "OUVERTE" : "fermee");
  ecran.printf("Alarme: %s", txtAlarme[alarme]);
  ecran.display();
}

// ============================ SETUP / LOOP ============================
void setup() {
  Serial.begin(115200);
  delay(200);
  base = String("maison-ia/") + MAISON_ID;
  journal("=== Maison intelligente — démarrage ===");

  pinMode(PIN_PRES_SALON, INPUT);
  pinMode(PIN_PRES_CHAMBRE, INPUT);
  pinMode(PIN_PORTE, INPUT_PULLUP);
  pinMode(PIN_BOUTON, INPUT_PULLUP);
  int sorties[] = {PIN_LUM_SALON, PIN_LUM_CHAMBRE, PIN_VENTILO, PIN_CHAUFFAGE,
                   PIN_LED_ARMEE, PIN_LED_ALARME, PIN_BUZZER};
  for (int p : sorties) { pinMode(p, OUTPUT); digitalWrite(p, LOW); }
  analogReadResolution(12);

  dht.setup(PIN_DHT, DHTesp::DHT22);

  ecranOk = ecran.begin(SSD1306_SWITCHCAPVCC, 0x3C);
  if (!ecranOk) journal("Écran OLED absent (ce n'est pas bloquant)");

  porteLue = porteOuverte = digitalRead(PIN_PORTE) == HIGH;

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_MDP, WIFI_CANAL);
  journal("Connexion au WiFi " WIFI_SSID "…");

  mqtt.setServer(MQTT_HOTE, MQTT_PORT);
  mqtt.setCallback(recevoirMessage);
  mqtt.setBufferSize(1024);  // l'état JSON dépasse les 256 octets par défaut
}

void loop() {
  unsigned long now = millis();

  lireCapteurs(now);
  lireBouton(now);
  majEnergie();
  majEclairage();
  majClimatisation(now);
  majAlarme(now);
  majSortiesAlarme(now);
  majBilanEnergie(now);
  gererReseau(now);

  if (etatModifie || now - dernierEtat >= PERIODE_ETAT_MS) {
    if (now - dernierEtat >= 250) {  // pas plus de 4 messages par seconde
      publierEtat();
      dernierEtat = now;
      etatModifie = false;
    }
  }
  if (now - dernierEcran >= 500) { dernierEcran = now; majEcran(); }

  delay(10);
}
