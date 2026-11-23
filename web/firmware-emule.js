/*
 * firmware-emule.js — MODE SECOURS HORS LIGNE uniquement.
 *
 * Traduction ligne à ligne de firmware/maison_intelligente/maison_intelligente.ino
 * (mêmes réglages que config.h). Elle sert seulement quand ni Wokwi ni la
 * maquette ne sont disponibles (pas d'Internet le jour de la présentation).
 * En mode normal, c'est le VRAI firmware ESP32 qui décide.
 */
(function () {
  const CFG = {
    SEUIL_NUIT: 40, HYST_LUMIERE: 10, DELAI_EXTINCTION_MS: 10000,
    CONSIGNE_DEFAUT: 24.0, HYST_CLIM: 1.0, DELAI_ABSENCE_CLIM_MS: 60000,
    DELAI_ENTREE_MS: 15000, DELAI_SORTIE_MS: 15000, SEUIL_GAZ: 60, SEUIL_ECO: 20,
    CONSO_BASE_W: 0.8, CONSO_LAMPE_W: 0.5, CONSO_VENTILO_W: 1.2, CONSO_CHAUFFAGE_W: 2.0,
  };
  const PIECES = ['salon', 'chambre'];

  class FirmwareEmule {
    constructor(bus) {
      this.bus = bus;
      this.ms = 0;
      this.virt = { pres_salon: 0, pres_chambre: 0, porte: 0, t: NaN, h: NaN, lum: 50, gaz: 0, solaire: 0, batterie: 100 };
      this.p = {};
      for (const n of PIECES) this.p[n] = { presence: false, occupee: false, lumiere: false, mode: 'auto', dejaVue: false, derniere: 0 };
      this.climAuto = true; this.consigne = CFG.CONSIGNE_DEFAUT; this.ventilo = false; this.chauffage = false;
      this.porteOuverte = false; this.alarme = 'desarmee'; this.cause = ''; this.debutVerif = 0; this.armeeDepuis = 0;
      this.eco = false; this.consoW = 0; this.wh = 0; this.whRef = 0;
      this.dernierEtat = -1e9; this.modifie = true;
      bus.on((sub, txt) => this.recevoir(sub, txt));
    }

    evenement(type, detail = '') { this.bus.publier('evenement', { type, detail }); }

    changerAlarme(e, cause = '') {
      if (e === this.alarme && cause === this.cause) return;
      this.alarme = e; this.cause = cause; this.modifie = true;
      if (e === 'armee') this.armeeDepuis = this.ms;
      if (e === 'verification') this.debutVerif = this.ms;
      this.evenement(e, cause);
    }

    resultatVision(connu) {
      const a = this.alarme;
      if (connu) {
        if (a === 'verification' || a === 'armee' || (a === 'declenchee' && this.cause !== 'gaz')) {
          this.changerAlarme('desarmee'); this.evenement('bienvenue', 'resident reconnu');
        }
      } else if (a === 'armee' || a === 'verification') this.changerAlarme('declenchee', 'intrus');
      else if (a === 'desarmee') this.evenement('visiteur', 'visage inconnu');
    }

    recevoir(sub, txt) {
      const m = String(txt).trim().toLowerCase();
      if (sub === 'capteurs/virtuels') { try { Object.assign(this.virt, JSON.parse(txt)); } catch (e) {} return; }
      if (sub === 'cmd/lumiere/salon' || sub === 'cmd/lumiere/chambre') this.p[sub.endsWith('salon') ? 'salon' : 'chambre'].mode = ['on', 'off'].includes(m) ? m : 'auto';
      else if (sub === 'cmd/clim') this.climAuto = m !== 'off';
      else if (sub === 'cmd/consigne') { const c = parseFloat(m); if (c >= 16 && c <= 30) this.consigne = c; }
      else if (sub === 'cmd/alarme') { if (m === 'armer') { if (this.alarme === 'desarmee') this.changerAlarme('armee'); } else if (m === 'desarmer' || m === 'stop') this.changerAlarme('desarmee'); }
      else if (sub === 'vision') { if (m.includes('inconnu')) this.resultatVision(false); else if (m.includes('connu')) this.resultatVision(true); }
      else return;
      this.modifie = true;
    }

    // Appelé à chaque image avec dt en secondes : équivalent de loop()
    boucle(dt) {
      const now = (this.ms += dt * 1000), v = this.virt;
      // lireCapteurs (source jumeau)
      const pres = { salon: !!v.pres_salon, chambre: !!v.pres_chambre };
      for (const n of PIECES) {
        const p = this.p[n];
        if (pres[n] !== p.presence) this.modifie = true;
        p.presence = pres[n];
        if (p.presence) { p.derniere = now; p.dejaVue = true; }
        p.occupee = p.presence || (p.dejaVue && now - p.derniere < CFG.DELAI_EXTINCTION_MS);
      }
      // majEnergie
      const eco = this.eco ? v.batterie < CFG.SEUIL_ECO + 5 : v.batterie < CFG.SEUIL_ECO;
      if (eco !== this.eco) { this.eco = eco; this.modifie = true; this.evenement('energie', eco ? 'mode eco active' : 'mode eco desactive'); }
      // majEclairage
      for (const n of PIECES) {
        const p = this.p[n];
        const sombre = v.lum < CFG.SEUIL_NUIT || (p.lumiere && v.lum < CFG.SEUIL_NUIT + CFG.HYST_LUMIERE);
        const voulu = p.mode === 'on' ? true : p.mode === 'off' ? false : p.occupee && sombre;
        if (voulu !== p.lumiere) { p.lumiere = voulu; this.modifie = true; }
      }
      // majClimatisation
      const recente = this.p.salon.dejaVue && now - this.p.salon.derniere < CFG.DELAI_ABSENCE_CLIM_MS;
      let ve = this.ventilo, ch = this.chauffage;
      if (!this.climAuto || this.eco || isNaN(v.t) || !recente) { ve = false; ch = false; }
      else {
        if (v.t >= this.consigne + CFG.HYST_CLIM) ve = true; else if (v.t <= this.consigne) ve = false;
        if (v.t <= this.consigne - CFG.HYST_CLIM) ch = true; else if (v.t >= this.consigne) ch = false;
      }
      if (ve !== this.ventilo || ch !== this.chauffage) { this.ventilo = ve; this.chauffage = ch; this.modifie = true; }
      // majAlarme
      const porte = !!v.porte, vientDOuvrir = porte && !this.porteOuverte;
      if (porte !== this.porteOuverte) { this.porteOuverte = porte; this.modifie = true; }
      if (v.gaz >= CFG.SEUIL_GAZ && !(this.alarme === 'declenchee' && this.cause === 'gaz')) this.changerAlarme('declenchee', 'gaz');
      const presence = pres.salon || pres.chambre;
      if (this.alarme === 'armee' && now - this.armeeDepuis > CFG.DELAI_SORTIE_MS) {
        if (vientDOuvrir) this.changerAlarme('verification', 'porte');
        else if (presence) this.changerAlarme('verification', 'presence');
      } else if (this.alarme === 'verification' && now - this.debutVerif > CFG.DELAI_ENTREE_MS) this.changerAlarme('declenchee', this.cause);
      // majBilanEnergie
      const h = dt / 3600, lampes = this.p.salon.lumiere + this.p.chambre.lumiere;
      this.consoW = CFG.CONSO_BASE_W + CFG.CONSO_LAMPE_W * lampes + CFG.CONSO_VENTILO_W * this.ventilo + CFG.CONSO_CHAUFFAGE_W * this.chauffage;
      const sombre = v.lum < CFG.SEUIL_NUIT, chaud = v.t >= this.consigne + CFG.HYST_CLIM, froid = v.t <= this.consigne - CFG.HYST_CLIM;
      const ref = CFG.CONSO_BASE_W + CFG.CONSO_LAMPE_W * 2 * sombre + CFG.CONSO_VENTILO_W * chaud + CFG.CONSO_CHAUFFAGE_W * froid;
      this.wh += this.consoW * h; this.whRef += ref * h;
      // publierEtat (même cadence que le firmware)
      if ((this.modifie && now - this.dernierEtat >= 250) || now - this.dernierEtat >= 2000) {
        this.dernierEtat = now; this.modifie = false;
        this.bus.publier('etat', this.etat());
      }
    }

    etat() {
      const v = this.virt, p = this.p;
      return {
        t: isNaN(v.t) ? null : +v.t.toFixed(1), h: isNaN(v.h) ? null : Math.round(v.h), lum: v.lum, gaz: v.gaz,
        pres: { salon: +p.salon.presence, chambre: +p.chambre.presence },
        lumiere: { salon: +p.salon.lumiere, chambre: +p.chambre.lumiere },
        mode_lum: { salon: p.salon.mode, chambre: p.chambre.mode },
        clim: { mode: this.climAuto ? 'auto' : 'off', consigne: this.consigne, ventilo: +this.ventilo, chauffage: +this.chauffage },
        porte: +this.porteOuverte, alarme: this.alarme, cause: this.cause,
        energie: { solaire_w: +(+v.solaire).toFixed(1), batterie: Math.round(v.batterie), eco: +this.eco, conso_w: +this.consoW.toFixed(2), wh: +this.wh.toFixed(3), wh_ref: +this.whRef.toFixed(3) },
        source: 'emule', uptime: Math.round(this.ms / 1000),
      };
    }
  }

  window.FirmwareEmule = FirmwareEmule;
})();
