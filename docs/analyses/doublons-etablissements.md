# Doublons d'établissements : analyse du 2026-11-18

## Méthode

La liste analysée est celle que chargent les migrations, reconstituée à partir des deux fichiers :

- `backend/alembic/donnees/annuaire.json` : 844 lignes, dont 838 après dédoublonnage, chargées par la spec 016.
  Noms accentués, sans préfecture ni ordre.
- `backend/alembic/donnees/etablissements_secondaire_1.json` : 2 396 lignes de la liste du ministère (spec 035).
  Préfecture et ordre renseignés, noms souvent sans accents.

Cela donne **2 780 établissements**, comme en préprod et en prod. Les établissements « proposés » par des présidents
n'en font pas partie : ils ne sont visibles qu'en base.

La migration de la spec 035 ne reconnaît un établissement existant qu'à **nom normalisé identique** (accents et casse
ignorés). Elle a donc créé un second établissement dès que la graphie différait d'un tiret, d'un « de », d'un chiffre
romain ou d'une lettre. Le cas était prévu par la spec 035 (« l'équipe repère et traite les doublons »).

Trois passes de détection :

1. **Clé forte.** Ponctuation retirée, « de/des/la/le » retirés, chiffres romains remplacés par des chiffres arabes,
   dans la même DRE.
2. **Nom proche.** Similarité d'au moins 0,88 sur le nom sans son sigle, dans la même IESG et avec la même famille de
   sigle.
3. **Clé phonétique.** k/c, ou/u, dj/dz/j et lettres doublées confondus, puis noms proches entre deux IESG d'une même
   DRE.

## Résultat

| Catégorie                                  | Paires | Action proposée           |
| ------------------------------------------ | -----: | ------------------------- |
| 1. Doublons certains                       |   ~120 | Fusion                    |
| 2. Doublons probables, à confirmer         |    ~15 | Confirmation par l'équipe |
| 3. Faux positifs, établissements distincts |    ~25 | Rien                      |

Dans la grande majorité des cas, l'un des deux vient de l'annuaire (le nom accentué, et peut-être des clubs ou des
membres) et l'autre de l'import (préfecture et ordre). **Règle proposée pour la fusion :**

- garder l'établissement de l'annuaire, avec son identifiant, son club et ses membres ;
- lui recopier la préfecture et l'ordre de l'import ;
- rattacher au gardé tout ce qui pointait vers l'autre (club, élèves, encadreurs) ;
- désactiver l'autre, sans le supprimer (`docs/RULES.md`).

Trois tables référencent un établissement : `club`, `eleve` et `encadreur`. Un seul club vivant est admis par
établissement (`uq_club_par_etablissement`) : si les deux établissements ont chacun un club vivant, la fusion
s'arrête et l'équipe tranche.

## 1. Doublons certains

Chaque ligne se lit « gardé (annuaire) ← absorbé (import) », sauf mention contraire. Entre crochets : l'IESG.

### Graphie seule : tiret, « de », chiffre romain ou arabe, accents (64 paires)

**Savanes**

- CEG Bogou 2 ← CEG Bogou II [Dapaong]
- CEG Dapaong Ville ← CEG Dapaong-Ville [Dapaong]
- CEG Kongo Moba ← CEG Kongo-Moba [Dapaong]
- CEG Namon-Dougba ← CEG Namon Dougba [Dapaong]
- CEG Sam Naba ← CEG Sam-Naba [Dapaong]
- CPL Bangré 2 ← CPL Bangre II [Dapaong]
- CPL Leaders ← CPL Les Leaders [Dapaong]
- CEG Mango Ville 1 ← CEG Mango Ville I [Mango]
- CEG Mango Ville 2 ← CEG Mango Ville II [Mango]
- CPL Millénium ← CPL Le Millenium [Mango]

**Kara**

- CEG Agbandé-Yaka ← CEG Agbande Yaka [Niamtougou]
- CEG Guérin-Kouka Sud ← CEG Guerin Kouka Sud [Bassar]
- CEG Kouméa 2 ← CEG Koumea II [Kara]
- CEG Lama Sahoudè ← CEG Lama-Sahoude [Kara]
- CEG Lassa-Soumdina ← CEG Lassa Soumdina [Kara]
- CEG Soumdina Bas ← CEG Soumdina-Bas [Kara]
- Lycée Guérin-Kouka I ← Lycée Guerin Kouka I [Bassar]
- Lycée Guérin-Kouka II ← Lycée Guerin Kouka II [Bassar]
- Lycée Kanté Ville 2 ← Lycée Kante Ville II [Niamtougou]
- Lycée Kara 1 ← Lycée Kara I [Kara]

**Centrale**

- CEG Adjengré 1 ← CEG Adjengre-I [Sotouboua]
- CEG Adjengré 2 ← CEG Adjengre II [Sotouboua]
- CEG Sotouboua Ville 2 ← CEG Sotouboua-Ville II [Sotouboua]
- CEG Filandi Somou ← CEG Filandi-Somou [Sokodé]
- CEG Kuwawu-Woro ← CEG Kuwawu Woro [Sokodé]
- Lycée Lama Tessi ← Lycée Lama-Tessi [Sokodé]
- Lycée Moderne Sokodé ← Lycée Moderne de Sokode [Sokodé]

**Plateaux Est**

- CEG A-ENS ← CEG A / Ens [Atakpamé]
- CEG Koéroma Djidjolé ← CEG Koeroma-Djidjole [Atakpamé]
- Lycée Aféyé-Kpota ← Lycée Afeye Kpota [Atakpamé]
- Lycée Amou-Oblo ← Lycée Amou Oblo [Atakpamé]
- CEG Notsé Ville 2 ← CEG Notse-Ville 2 [Notsé]
- Collège Protestant de TADO ← Collège Protestant Tado [Notsé]
- Lycée de Wahala ← Lycée Wahala [Notsé]
- Lycée Kpégnon-Adja ← Lycée de Kpegnon-Adja [Notsé]
- Lycée Kpékplémé ← Lycée de Kpekpleme [Notsé]
- Lycée Tohoun ← Lycée de Tohoun [Notsé]

**Plateaux Ouest**

- CEG Agou Gare ← CEG Agou-Gare [Kpalimé]
- CEG Kuma Tokpli ← CEG Kuma-Tokpli [Kpalimé]
- Lycée de 2 Nyogbo ← Lycée des 2 Nyogbo [Kpalimé]
- Lycée de Zomayi ← Lycée Zomayi [Kpalimé]
- CEG Amégapé Nyamégbé ← CEG D'Amegape Nyamegbe [Adéta]
- Lycée Danyi Elavanyo ← Lycée Danyi-Elavanyo [Adéta]
- CEG Badou Ville ← CEG Badou-Ville [Badou]
- Lycée Veh N’kougna ← Lycée Veh-N'Kougna [Badou]

**Maritime**

- CEG Gapé Kpédji ← CEG Gape-Kpedji [Tsévié]
- Lycée Dzolo ← Lycée de Dzolo [Tsévié]
- CEG Kouvé - Atran ← CEG Kouve-Atran [Vogan]
- Lycée Vo Afowimé ← Lycée Vo-Afowime [Vogan]
- Lycée Vo Attivé ← Lycée Vo-Attive [Vogan]
- Lycée Vo Koutimé ← Lycée Vo-Koutime [Vogan]
- CEG Séwatsri-Kopé ← CEG Sewatsri Kope [Aného]
- Lycée Gbodjomé ← Lycée de Gbodjome [Aného]
- CEG La Solidarité ← CEG Solidarité [Aného] _(les deux viennent de l'annuaire ; garder celui qui a une préfecture)_

**Grand Lomé**

- Lycée Aflao-Lankouvi ← Lycée Aflao Lankouvi [Golfe]
- Lycée Avédji-Elavagnon ← Lycée Avedji Elavagnon [Golfe]
- Lycée Bè Klikamé ← Lycée Be-Klikame [Golfe]
- Lycée de Tokoin I ← Lycée Tokoin I [Golfe]
- Lycée de Tokoin II ← Lycée Tokoin II [Golfe]
- Lycée Kodjoviakopé ← Lycée de Kodjoviakope [Golfe]
- Lycée Nyékonakpoé ← Lycée de Nyekonakpoe [Golfe]
- Lycée Tokoin Est ← Lycée Tokoin-Est [Golfe]
- Lycée Agoè Nord ← Lycée Agoe-Nord [Agoényivé]
- CPL Life Shaping ← CPL Life-Shaping [Golfe] _(deux lignes de l'import)_

### Une lettre de différence ou faute de frappe (environ 55 paires)

**Savanes**

- CEG Dassouté Nank ← CEG Dassoute-Nanik [Dapaong]
- CEG Warkanbou ← CEG Warkambou [Dapaong]
- CEG Lokpanou ← CEG Lokpano [Dapaong]
- CEG Tambago ← CEG Tambango [Dapaong]
- CPL Afo Lofa ← CPL Afo Loffa [Dapaong]
- CEGIL Gabongbon ← CEGIL Gabongbong [Dapaong]
- CEG Galangashi ← CEG Galangashie [Mango]
- Lycée Sagbiégou ← Lycée Sagbiebou [Mango]
- Lycée Koudjoaré [Grand Kpendjal] ← Lycée Koundjoare [Mango] _(IESG différentes : déjà constaté par la spec 035)_
- CEG Malgbangou [Grand Kpendjal] ← CEG Malgbongou [Mango] _(idem)_

**Kara**

- CEG Sirka Ndjei ← CEG Sirka N'Djei [Kara]
- Lycée Sarakawa ← Lycée Sara Kawa [Kara]
- Lycée Soundina Haut ← Lycée Soumdina-Haut [Kara]
- CEG Tchanadè ← CEG Tchannade [Kara]
- CEG Gninguélia ← CEG Gniguelia [Kara]
- Lycée Sola ← Lycée Solla [Kara]
- CEG Akpont ← CEG Akponte [Niamtougou]
- Lycée Kadjala ← Lycée Kadjalla [Niamtougou]
- CEG Ossakré ← CEG Ossacre [Niamtougou]

**Centrale**

- CEG Ahaloukpaboudou ← CEG Haloukpaboundou [Sotouboua]
- CEG Babdé ← CEG Babade [Sotouboua]
- CEG Assokoko ← CEG Assoukoko [Sotouboua]
- Lycée Yaloubè ← Lycée Yaloumbe [Sotouboua]
- CEG Didaouré ← CEG Didaure [Sokodé]

**Plateaux Est**

- CEG Bassi-Ogbotanawlou ← CEG Basse-Ogbatanawlou [Atakpamé]
- CEG Yao Kopé ← CEG Yao-Cope [Atakpamé]
- CEG Palakoko ← CEG Pallakoko [Anié]
- CEG Atcinédji ← CEG Atchinedji [Anié]
- CEG Gbégnafé Sanda ← CEG Gbegnafe Sada [Anié]
- Lycée Kolocopé ← Lycée Kolo Cope [Anié]
- CEG Agbondi ← CEG Agbondji [Notsé]
- Lycée Atitsohoé-Dzekloé ← Lycée Atitsohoe Djekloe [Notsé]

**Plateaux Ouest**

- CEG Agou Kébotoé ← CEG Agou-Kebo-Toe [Kpalimé]
- CEG Assahoun Flagbé ← CEG Assahoun-Fiagbe [Kpalimé]
- CEG Gadzagan ← CEG Gadjagan [Kpalimé]
- Lycée Tové Rail ← Lycée Tove Rails [Kpalimé]
- Lycée d’Amouzoukopé ← Lycée Amousoukope [Kpalimé]
- CEG Mama Kopé ← CEG Mamakope [Adéta]
- CEG Dzogbégan Mempeassem ← CEG Danyi Dzogbegan Mempeassem [Adéta]
- CEG Danyi Apéyémé ← CEG Danyi Apeyeyeme [Adéta]
- CEG Danyi Afiadenyigban ← CEG Danyi Afiadenyigba [Adéta]
- Lycée Ahlon Sasanou ← Lycée Ahlon Sassanou [Adéta]
- Lycée Klabè-Efoukpa ← Lycée Klabe Efukpa [Badou]

**Maritime**

- CEG Kondokopé ← CEG Kondo Copé (annuaire) et CEG Kondocope (import) [Tsévié] _(trois fiches pour un seul établissement)_
- CEG Baka Copé ← CEG Baka-Kope [Tsévié]
- CEG Gapé Dzatipko ← CEG Gape Dzatikpo [Tsévié]
- Lycée Djogblakopé ← Lycée Dzogblakope [Tsévié]
- CEG Doklala ← CEG Dokplala [Tsévié]
- CEG Liliopé ← CEG Lilikope [Tsévié]
- CEG Yotokopé ← CEG Yoto-Kope [Vogan]
- CEG Goumoukopé ← CEG Goumoucope [Aného]
- CEG Alouénou Kpétdto ← CEG Alouenou Kpeteto [Aného]
- CEG Zoti Novissi ← CEG Zooti Novissi [Aného]

Le nom de l'annuaire contient parfois une faute que le fichier du ministère corrige : « Kpétdto », « Liliopé »,
« Flagbé », « Gapé Dzatipko ». Lors de la fusion, on garde l'identifiant de l'annuaire mais il vaut mieux reprendre le
nom du ministère, en remettant ses accents.

## 2. Doublons probables, à confirmer par l'équipe

- Lycée Attidjin ← Lycée Attidjin (PC) [Tsévié] ; Lycée Agbélouvé ← Lycée Agbelouve(PC) [Tsévié]. Il faut savoir ce
  que signifie « (PC) » : une section ou un établissement à part ?
- Lycée Kouma ← Lycée Kuma [Kpalimé]
- Lycée Kpinzindé ← Lycée Kpanzinde [Kara]
- CEG Akpoguédjé ← CEG Okpoguedje [Anié]
- CEG Gapé Adzidi ← CEG Gape-Adzido [Tsévié]
- Lycée Kpalla / Lycée Kpala [Tsévié] : les deux viennent de l'annuaire.
- Lycée Adjégré / Lycée Adjengré [Sotouboua] : les deux viennent de l'annuaire.
- CEG Djapal / CEG Djapalé [Dapaong] : les deux viennent de l'annuaire.
- CEG Elavagnon [Atakpamé] / CEG Elavagnon [Anié], avec en plus un CEG Elavagnon 2 [Anié] : les trois viennent de
  l'annuaire, et l'import n'a complété que celui d'Anié.
- CPL CITAPA (annuaire) ← CPI Citapa (import, privé islamique) [Kpalimé] : l'annuaire s'est sans doute trompé de
  sigle.
- CPL Le Bon Berger (laïc) / CPE Bon Berger (protestant) [Tsévié] : deux lignes de l'import.
- CPL Cle des Savoirs / CPL La Cle du Savoir [Tsévié] ; CPL Le Guide / CPL La Guidee [Agoényivé] : lignes de
  l'import.
- Même nom dans deux IESG voisines de Lomé (Golfe et Agoényivé) : CPL Alfred Nobel, CPL Aube Nouvelle, CPL Le Relais,
  CPL Le Trésor, CPL Les Élites de Demain, CPL Schekina, CPL Sinai / Le Sinai, CPL Espérance / CS Espérance,
  CPL Le Petit Prince / Le Petit Prince J. Il peut s'agir d'**annexes** du même promoteur, qu'il faudrait alors
  garder séparées. Le ministère les liste deux fois, il faut donc vérifier sur le terrain.

## 3. Faux positifs : établissements distincts, à garder

- Numéros ou groupes différents : CPL La Fabienne I / III / M / A ; CPL Saint Charbel N°1 / II ;
  CPL Bernard B. Dadie / Dadier II ; CPL Nouvelle Élite I / II ; CPI Daroul Hikmah I / IV / 5 et CPL Daroul Hikmah 3 ;
  CPL Le Souverain G/A / G/B ; CPL Solidarite G/A / G/B.
- Annexe : CPL Le Jardin de la Connaissance et de l'Excellence et sa version « (Annexe) ».
- Localités différentes :
  - CEG Bassar Est / Ouest ;
  - CEG Gape-Kpedji / Gape-Kpodji ;
  - CEG Vo-Tekponou / Vo-Kponou ;
  - Lycée Borgou (Kpendjal) / Lycée Bogou (Tandjouaré) ;
  - CPL La Réussite (Vo et Zio) ;
  - Complexe Scolaire les Élites (Amou et Haho) ;
  - CPE / CPL La Confiance (Yoto et Zio) ;
  - CPL La Sagesse / Les Sages.

## Limites

- Les noms d'établissements identiques dans deux DRE différentes ne sont pas signalés : ils désignent en général deux
  villes différentes.
- Les établissements « proposés » par les présidents et ceux créés par l'équipe dans le back office ne figurent pas
  dans cette analyse. Il faudra relancer la détection sur la base de prod, en lecture seule, depuis le serveur.
- Au-dessous d'un seuil de similarité de 0,88, des doublons à l'orthographe très éloignée peuvent avoir échappé à la
  détection.
- Le nombre de clubs, d'élèves et d'encadreurs rattachés à chaque doublon n'est pas connu ici. La base locale n'était
  pas démarrée, et la prod ne se lit pas depuis le poste de développement.
