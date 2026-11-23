# Protection des données (RGPD)

La caméra traite des visages, qui sont des **données biométriques**, une catégorie particulièrement protégée par le RGPD. Voici comment le projet limite les risques. Ces mesures relèvent de bonnes pratiques ; elles ne remplacent pas un avis juridique.

| Principe | Mesure dans le projet |
|---|---|
| **Consentement** | Chaque résident est enregistré volontairement (`enroler.py`), avec son accord |
| **Minimisation** | Aucune photo des résidents n'est conservée, seulement des empreintes numériques (128 nombres) |
| **Stockage local** | Les empreintes restent sur le PC (`vision/donnees/visages.npz`), exclues de GitHub par `.gitignore` |
| **Pas de nom sur le réseau** | Seuls « connu » ou « inconnu » transitent par MQTT |
| **Photos limitées** | Une photo n'est envoyée que pendant une alarme, et uniquement au propriétaire (Telegram privé). Rien n'est enregistré sur le disque |
| **Droit à l'effacement** | `python enroler.py --supprimer Marie` efface définitivement la personne |
| **Périmètre** | La caméra filme la porte d'entrée de la propriété, pas la voie publique |
| **Information** | Une affichette « Zone sous vidéoprotection » est à placer près de la porte |
| **Autonomie** | Si la caméra ou Internet tombe en panne, l'alarme fonctionne toujours (contact de porte, radar, bouton) |

**Phrase pour le jury** : « Notre caméra reconnaît les résidents sans jamais stocker leur photo ni envoyer leur nom sur Internet : seules des empreintes mathématiques restent sur l'ordinateur de la maison. »
