# Guide pour présenter et défendre le projet

## 1. Organisation à deux (15 minutes + questions)

| Temps | Diapositives | Qui parle | Contenu |
|---|---|---|---|
| 0:00 – 2:00 | 1 à 4 | Personne A | Présentation, les 3 problèmes, la solution, la méthode « virtuel puis FabLab » |
| 2:00 – 5:30 | 5 à 11 | Personne B | Le cerveau ESP32, puis le confort : radar, LDR, LED, DHT22, relais et ventilateur |
| 5:30 – 9:00 | 12 à 17 | Personne A | La sécurité : caméra, vision par ordinateur, ILS, MQ-2, alertes, logique de l'alarme |
| 9:00 – 10:30 | 18 à 21 | Personne B | L'énergie, le bilan d'économie, le site et MQTT |
| 10:30 – 13:30 | 22 | A pilote, B commente | **Démonstration en direct** |
| 13:30 – 15:00 | 23 à 26 | Ensemble | FabLab, budget, limites, conclusion |

Règle d'or : celui qui ne parle pas **pilote l'ordinateur** et prépare la suite. On ne se coupe pas la parole ; on se passe le relais par une phrase (« Je laisse X vous présenter la sécurité »).

## 2. La structure de chaque diapositive de composant

Pour chaque composant, dites toujours trois choses, dans cet ordre :
1. **Ce que c'est** (montrez la photo) : « Voici un DHT22. »
2. **Son rôle dans la maison** : « Il mesure la température du séjour. »
3. **Comment il fonctionne**, en une phrase simple : « Une thermistance change de résistance avec la chaleur. »

Les notes de l'orateur (touche **N** dans la présentation) contiennent les phrases clés et les arguments.

## 3. Le scénario de démonstration (à répéter 3 fois)

1. Ouvrez le jumeau 3D (mode Simulation avec Wokwi, ou Hors ligne en secours) et le site de contrôle sur un téléphone.
2. Lancez **Scénario de présentation** et commentez chaque étape. Le scénario se met en pause entre deux légendes : prenez le temps.
3. Démonstration interactive :
   - sur le téléphone, armez l'alarme : le jumeau 3D et le site passent en « Armée » ;
   - un membre enregistré passe devant la webcam : il est reconnu et l'alarme se désarme ;
   - une personne du public (non enregistrée) passe : la sirène se déclenche et la notification Telegram arrive ;
   - appuyez 2 s sur **SOS** sur le téléphone : l'alarme se déclenche dans la 3D.
4. Montrez l'onglet **Analyses** : courbes en temps réel et pourcentage d'économie.

**Plan B** : si Internet tombe, passez le jumeau et le site en mode **Hors ligne** (même navigateur). Si la webcam ne marche pas, utilisez la vision simulée de la 3D. Annoncez-le calmement : « Nous basculons sur le mode de secours, prévu pour ce cas. » Le fait d'avoir prévu un plan B est en soi un argument.

## 4. Questions probables du jury et réponses

| Question | Réponse courte |
|---|---|
| Pourquoi un ESP32 et pas un Arduino ? | Le WiFi est intégré, il est 15 fois plus rapide, il coûte à peu près pareil et se programme avec le même logiciel. |
| Pourquoi un radar et pas un capteur PIR ? | Le PIR ne voit que le mouvement : une personne qui lit sans bouger serait « absente ». Le radar détecte la respiration. |
| Et si Internet est coupé ? | L'ESP32 prend toutes les décisions localement : lumière, climatisation et alarme continuent de fonctionner. Internet sert seulement au téléphone. |
| Et si la caméra tombe en panne ? | Le contact de porte et le radar suffisent à déclencher l'alarme après 15 s. La caméra sert à éviter les fausses alarmes pour les résidents. |
| Comment fonctionne la reconnaissance faciale ? | Un réseau de neurones trouve les visages (YuNet), un deuxième les transforme en 128 nombres (SFace), puis on compare avec les résidents (similarité cosinus, seuil 0,363). |
| Et la vie privée ? | Aucune photo des résidents n'est stockée, seulement leur empreinte numérique, sur le PC. Aucun nom ne circule sur Internet. Chacun peut être effacé. |
| Une photo devant la caméra peut-elle tromper le système ? | Oui, c'est une limite connue. Une amélioration serait la détection de vivacité (clignement des yeux, caméra de profondeur). |
| Comment prouvez-vous l'économie d'énergie ? | L'ESP32 compare en continu la consommation réelle à celle d'une maison sans automatisme, avec les mêmes conditions. |
| Votre système est-il sécurisé ? | Pour la démonstration, le broker est public, protégé par un identifiant secret. Pour une vraie maison : broker privé, mot de passe, chiffrement TLS. |
| Pourquoi simuler avant de construire ? | Pour tester et corriger sans casser de matériel ; et parce que le même code passe ensuite tel quel sur la vraie carte. |
| Qu'avez-vous appris ? | Préparez chacun une réponse personnelle et sincère : programmation, électronique, travail en équipe, gestion d'un imprévu. |

Si vous ne connaissez pas une réponse : « Bonne question, nous ne l'avons pas encore testé ; voici comment nous le vérifierions… » Ne jamais inventer.

## 5. Conseils pour l'oral

- **Regardez le public**, pas l'écran : les notes sont là pour vous rassurer, pas pour être lues.
- **Une idée par phrase**, des phrases courtes. Évitez les sigles non expliqués (dites « protocole de messages MQTT » la première fois).
- **Montrez du doigt** l'objet dont vous parlez dans la 3D ou sur la maquette.
- **Chronométrez** les répétitions : 15 minutes, c'est vite atteint.
- **Arrivez 20 minutes avant** : testez le Wi-Fi de la salle, la webcam, le téléphone et le son de la sirène.

## 6. Liste de contrôle du jour J

- [ ] Batterie du PC et du téléphone chargées, chargeur dans le sac
- [ ] Pages ouvertes : présentation, jumeau 3D, site de contrôle (téléphone)
- [ ] Wokwi lancé, pastille verte « Firmware ESP32 · capteurs 3D »
- [ ] `surveillance.py` lancé, les deux membres enregistrés, Telegram testé
- [ ] Identifiant de maison secret partout
- [ ] Plan B testé : mode Hors ligne
- [ ] Les noms remplis sur la première diapositive
