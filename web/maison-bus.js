/*
 * maison-bus.js — Connexion commune au jumeau 3D et au site de contrôle.
 *
 *  - Transport "mqtt"  : broker MQTT public (WebSocket sécurisé), le même que
 *                        celui de l'ESP32 et du programme Python.
 *  - Transport "local" : BroadcastChannel entre onglets du même navigateur,
 *                        pour le mode hors ligne (aucun Internet nécessaire).
 *
 *  Les topics sont identiques dans les deux cas : maison-ia/<id>/...
 */
(function () {
  const BROKER_WSS = 'wss://broker.hivemq.com:8884/mqtt';

  class MaisonBus {
    constructor() {
      this.ecouteurs = [];
      this.surStatut = () => {};
      this.transport = null;
      this.base = '';
      this.client = null;
      this.canal = null;
      this.connecte = false;
    }

    // fn(sousTopic, texte) — ex. fn('etat', '{"t":24.1,...}')
    on(fn) { this.ecouteurs.push(fn); }
    _recevoir(sub, texte) { for (const fn of this.ecouteurs) { try { fn(sub, texte); } catch (e) { console.error(e); } } }

    connecter(transport, id) {
      this.fermer();
      this.transport = transport;
      this.base = 'maison-ia/' + id;
      if (transport === 'local') {
        if (!('BroadcastChannel' in window)) { this.surStatut('erreur', 'Navigateur trop ancien'); return; }
        this.canal = new BroadcastChannel('maison-ia');
        this.canal.onmessage = (e) => {
          const { topic, texte } = e.data || {};
          if (topic && topic.startsWith(this.base + '/')) this._recevoir(topic.slice(this.base.length + 1), texte);
        };
        this.connecte = true;
        this.surStatut('ok', 'Mode hors ligne (local)');
        return;
      }
      if (!window.mqtt) { this.surStatut('erreur', 'Bibliothèque MQTT non chargée : pas d\'Internet ?'); return; }
      this.surStatut('attente', 'Connexion au broker MQTT…');
      try {
        this.client = window.mqtt.connect(BROKER_WSS, {
          clientId: 'web-' + Math.random().toString(16).slice(2, 10), reconnectPeriod: 4000, connectTimeout: 8000, clean: true,
        });
      } catch (e) { this.surStatut('erreur', e.message); return; }
      this.client.on('connect', () => {
        this.connecte = true;
        this.client.subscribe(this.base + '/#');
        this.surStatut('ok', 'Connecté au broker MQTT');
      });
      this.client.on('reconnect', () => this.surStatut('attente', 'Reconnexion…'));
      this.client.on('offline', () => { this.connecte = false; this.surStatut('erreur', 'Broker injoignable (Internet ? page ouverte depuis GitHub Pages ou un serveur local ?)'); });
      this.client.on('error', (e) => this.surStatut('erreur', 'Erreur MQTT : ' + (e.message || e)));
      this.client.on('message', (topic, buf) => this._recevoir(topic.slice(this.base.length + 1), buf.toString()));
    }

    publier(sub, contenu, retenu = false) {
      const texte = typeof contenu === 'string' ? contenu : JSON.stringify(contenu);
      const topic = this.base + '/' + sub;
      if (this.transport === 'local' && this.canal) {
        this.canal.postMessage({ topic, texte });
        this._recevoir(sub, texte);  // MQTT renvoie aussi nos propres messages
      } else if (this.client && this.connecte) {
        this.client.publish(topic, texte, { retain: retenu });
      } else return false;
      return true;
    }

    fermer() {
      if (this.client) { try { this.client.end(true); } catch (e) {} }
      if (this.canal) this.canal.close();
      this.client = this.canal = null;
      this.connecte = false;
    }
  }

  window.MaisonBus = MaisonBus;
})();
