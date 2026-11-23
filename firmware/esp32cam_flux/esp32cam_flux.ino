/*
 * =====================================================================
 *  ESP32-CAM — caméra de l'entrée de la maquette (FabLab)
 * =====================================================================
 *  Diffuse la vidéo en WiFi : http://<adresse IP>:81/stream
 *  Le programme Python (vision/surveillance.py) lit ce flux et fait la
 *  reconnaissance faciale sur le PC : l'ESP32-CAM n'est pas assez
 *  puissante pour le faire elle-même.
 *
 *  Carte : « AI Thinker ESP32-CAM » dans l'IDE Arduino.
 *  Téléversement : programmateur USB-série (ou carte ESP32-CAM-MB),
 *  GPIO 0 relié à GND pendant le téléversement, puis débranché.
 *
 *  Dans vision/config.ini :  source = http://<adresse IP>:81/stream
 * =====================================================================
 */
#include "esp_camera.h"
#include <WiFi.h>
#include "esp_http_server.h"

// ----------- À MODIFIER : WiFi du FabLab / de la maison ---------------
const char* WIFI_SSID = "Nom_du_wifi";
const char* WIFI_MDP  = "mot_de_passe";

// ----------- Broches de la carte AI Thinker ---------------------------
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22
#define LED_FLASH          4   // LED blanche intégrée (éclairage de nuit)

#define LIMITE "maisoniaflux"
static const char* TYPE_FLUX = "multipart/x-mixed-replace;boundary=" LIMITE;
static const char* SEPARATEUR = "\r\n--" LIMITE "\r\n";
static const char* ENTETE_IMAGE = "Content-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n";

static esp_err_t flux_video(httpd_req_t* req) {
  char entete[64];
  esp_err_t res = httpd_resp_set_type(req, TYPE_FLUX);
  if (res != ESP_OK) return res;
  httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");
  while (true) {
    camera_fb_t* image = esp_camera_fb_get();
    if (!image) { Serial.println("Capture impossible"); return ESP_FAIL; }
    size_t n = snprintf(entete, sizeof(entete), ENTETE_IMAGE, image->len);
    res = httpd_resp_send_chunk(req, SEPARATEUR, strlen(SEPARATEUR));
    if (res == ESP_OK) res = httpd_resp_send_chunk(req, entete, n);
    if (res == ESP_OK) res = httpd_resp_send_chunk(req, (const char*)image->buf, image->len);
    esp_camera_fb_return(image);
    if (res != ESP_OK) break;  // le client s'est déconnecté
  }
  return res;
}

static esp_err_t photo(httpd_req_t* req) {
  camera_fb_t* image = esp_camera_fb_get();
  if (!image) { httpd_resp_send_500(req); return ESP_FAIL; }
  httpd_resp_set_type(req, "image/jpeg");
  httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");
  esp_err_t res = httpd_resp_send(req, (const char*)image->buf, image->len);
  esp_camera_fb_return(image);
  return res;
}

static esp_err_t flash(httpd_req_t* req) {  // /flash?on=1
  char q[16] = {0}, v[4] = {0};
  if (httpd_req_get_url_query_str(req, q, sizeof(q)) == ESP_OK && httpd_query_key_value(q, "on", v, sizeof(v)) == ESP_OK)
    digitalWrite(LED_FLASH, v[0] == '1' ? HIGH : LOW);
  httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");
  return httpd_resp_sendstr(req, "ok");
}

void demarrerServeur() {
  httpd_config_t config = HTTPD_DEFAULT_CONFIG();
  config.server_port = 81;
  config.ctrl_port = 32769;
  httpd_handle_t serveur = NULL;
  if (httpd_start(&serveur, &config) != ESP_OK) { Serial.println("Serveur impossible à démarrer"); return; }
  httpd_uri_t uFlux  = { "/stream",  HTTP_GET, flux_video, NULL };
  httpd_uri_t uPhoto = { "/capture", HTTP_GET, photo,      NULL };
  httpd_uri_t uFlash = { "/flash",   HTTP_GET, flash,      NULL };
  httpd_register_uri_handler(serveur, &uFlux);
  httpd_register_uri_handler(serveur, &uPhoto);
  httpd_register_uri_handler(serveur, &uFlash);
}

void setup() {
  Serial.begin(115200);
  pinMode(LED_FLASH, OUTPUT);
  digitalWrite(LED_FLASH, LOW);

  camera_config_t c = {};
  c.ledc_channel = LEDC_CHANNEL_0;
  c.ledc_timer   = LEDC_TIMER_0;
  c.pin_d0 = Y2_GPIO_NUM; c.pin_d1 = Y3_GPIO_NUM; c.pin_d2 = Y4_GPIO_NUM; c.pin_d3 = Y5_GPIO_NUM;
  c.pin_d4 = Y6_GPIO_NUM; c.pin_d5 = Y7_GPIO_NUM; c.pin_d6 = Y8_GPIO_NUM; c.pin_d7 = Y9_GPIO_NUM;
  c.pin_xclk = XCLK_GPIO_NUM; c.pin_pclk = PCLK_GPIO_NUM;
  c.pin_vsync = VSYNC_GPIO_NUM; c.pin_href = HREF_GPIO_NUM;
  c.pin_sccb_sda = SIOD_GPIO_NUM; c.pin_sccb_scl = SIOC_GPIO_NUM;
  c.pin_pwdn = PWDN_GPIO_NUM; c.pin_reset = RESET_GPIO_NUM;
  c.xclk_freq_hz = 20000000;
  c.pixel_format = PIXFORMAT_JPEG;
  c.frame_size   = FRAMESIZE_VGA;      // 640×480 : bon compromis vitesse / reconnaissance
  c.jpeg_quality = 12;                 // 10 = meilleure qualité, 63 = plus léger
  c.fb_count     = psramFound() ? 2 : 1;
  c.fb_location  = psramFound() ? CAMERA_FB_IN_PSRAM : CAMERA_FB_IN_DRAM;
  c.grab_mode    = CAMERA_GRAB_LATEST; // toujours l'image la plus récente

  if (esp_camera_init(&c) != ESP_OK) {
    Serial.println("Caméra non détectée : vérifiez la nappe du capteur OV2640.");
    delay(3000);
    ESP.restart();
  }
  sensor_t* s = esp_camera_sensor_get();
  s->set_vflip(s, 1);    // retourner l'image si la caméra est montée à l'envers
  s->set_hmirror(s, 1);

  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);  // évite les saccades du flux
  WiFi.begin(WIFI_SSID, WIFI_MDP);
  Serial.print("Connexion WiFi");
  while (WiFi.status() != WL_CONNECTED) { delay(400); Serial.print("."); }
  Serial.println();
  demarrerServeur();
  Serial.print("Flux vidéo : http://");
  Serial.print(WiFi.localIP());
  Serial.println(":81/stream");
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) { WiFi.reconnect(); delay(5000); }  // reconnexion automatique
  delay(1000);
}
