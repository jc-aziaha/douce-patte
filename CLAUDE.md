# Douce Patte — Site vitrine + chatbot IA

Site vitrine pour Manon Dubois, auto-entrepreneuse en garde et promenade d'animaux (chiens et chats). Développé par Yanis Belkacem (prestataire).

**État du projet :**

- **Phase 1 — site vitrine : en production.** 8 pages, formulaire de contact fonctionnel, déployé sur Render.
- **Phase 2 — chatbot IA (RAG) : en développement.** Objet d'un avenant au cahier des charges. C'est le travail en cours.

## Documents de référence

Ce dossier (`6-developpement-et-tests`) contient le code. Les documents de cadrage sont dans les dossiers voisins (`..\`) :

**Phase 1**
- `..\2-cahier des charges\2a-redaction-du-cahier-des-charges.docx` — périmètre contractuel signé (v1.0)
- `..\3-specifications-fonctionnelles\3a-specifications-fonctionnelles.docx` — comportement attendu (v3.0)
- `..\4-conception-ux-ui\4a-maquette-douce-patte.html` — maquette validée
- `..\5-specifications-techniques\5-specifications-techniques.md` — choix d'implémentation (v3.0)

**Phase 2 — chatbot**
- `..\2-cahier des charges\` — avenant chatbot (périmètre, budget, RGPD)
- `..\3-specifications-fonctionnelles\10-specifications-fonctionnelles-chatbot-ia.md` — comportement attendu (v1.1)
- `..\5-specifications-techniques\12-specifications-techniques-chatbot-ia.md` — architecture et sécurité (v2.0)
- `..\4-conception-ux-ui\4a-maquette-douce-patte.html` — page « Chatbot IA » du canvas : widget en contexte + états

**Toujours se référer à ces documents avant de trancher un point de comportement, de contenu ou de design.** Ne pas réinterpréter le périmètre ni ajouter de fonctionnalité qui n'y figure pas.

## Résumé du projet

- 5 services : promenade de chiens, visites à domicile pour chats, garde pendant les vacances, passage nourriture/eau, garde ponctuelle en journée.
- 8 pages : Accueil, Services, À propos, Questions fréquentes (FAQ), Contact, Mentions légales, Politique de confidentialité, Cookies.
- Formulaire de contact : nom, email, téléphone, service souhaité (obligatoires), message (facultatif) → email de notification à Manon, **aucune donnée stockée**.
- Pas de compte utilisateur, pas de CRM, pas de back-office.
- Domaine : `douce-patte.fr`. Hébergement : Render (**plan gratuit**). Dépôt : GitHub, sous le compte de Manon.

## Stack technique

- **Frontend** : HTML / CSS / JS natifs, sans framework. GSAP en `defer`, respecte `prefers-reduced-motion`.
- **Backend** : Python 3.12+, FastAPI, Pydantic. Service unique : l'API sert aussi les fichiers statiques du frontend.
- **Base de données : aucune.** Ni en phase 1, ni en phase 2.
- **Anti-spam du formulaire** : honeypot + Google reCAPTCHA v3 (invisible).
- **Email** : Mailtrap en développement, Brevo en production.
- **IA (phase 2)** : Gemini (Google), pour les embeddings et la génération. Fournisseur unique. Identifiants de modèles **en variables d'environnement**, jamais codés en dur — ils évoluent vite chez ce fournisseur.
- **Build** : esbuild (JS) et Lightning CSS.
- **Tests** : pytest (unitaires + intégration via TestClient), Playwright (fonctionnels), pytest-cov.
- **Analyse statique** : Ruff + Pyright (Python), W3C + Stylelint + ESLint (frontend).
- **Déploiement** : Render, manuel (pas de CI/CD).

## Phase 2 — Chatbot IA (RAG)

Objectif : réduire les questions répétitives adressées à Manon, en répondant à partir du contenu déjà publié sur le site.

### Contrainte structurante : Render plan gratuit

512 Mo de RAM (dont ~100 déjà utilisés), CPU fractionné, mise en veille après 15 min avec un réveil d'environ une minute, système de fichiers **éphémère**. Le passage à un plan payant est connu et assumé comme une évolution ultérieure — **le code doit fonctionner sur le plan gratuit**.

**Aucun modèle d'IA ne tourne sur le serveur.** Pas de `chromadb`, pas d'`onnxruntime`, pas de `sentence-transformers`, pas de `torch`.

### Architecture retenue

- Le corpus (FAQ, services, tarifs, zone d'intervention, moyens de paiement) est découpé en passages courts et autonomes.
- Les embeddings du corpus sont calculés **une seule fois, en local**, par `scripts/build_index.py`.
- L'index est un **fichier `.npz` versionné dans le dépôt** (~180 Ko), chargé en mémoire au démarrage. Il survit ainsi au système de fichiers éphémère.
- **Dimension des embeddings : 768** (le modèle en accepte de 128 à 3 072 ; 768 suffit pour ce corpus et divise la taille de l'index).
- À l'exécution, le serveur ne calcule que le vecteur de la question, puis fait une **similarité cosinus en mémoire (numpy)**. Pas de base vectorielle.
- Le nom du modèle **et la dimension** sont stockés dans l'index et vérifiés au démarrage : en cas de divergence avec la configuration, le démarrage échoue explicitement plutôt que de produire des résultats silencieusement faux. Tout changement de modèle impose une réindexation complète.

### Règles non négociables

1. **Le seuil de pertinence est un mécanisme, pas une consigne.** Si le meilleur score de similarité est sous le seuil, la réponse « hors périmètre » part directement, **sans appel au modèle de génération**. La règle « ne jamais inventer » ne repose jamais sur le seul prompt système.
2. **Aucune branche ne renvoie d'erreur visible au visiteur.** Panne fournisseur, plafond atteint, question hors sujet, délai dépassé : tous produisent une réponse utile, avec renvoi vers le formulaire de contact.
3. **Le statut vient du serveur.** La réponse porte un champ `status` (`answered` / `out_of_scope`) qui commande l'état visuel « À confirmer avec Manon ». Le frontend ne le devine jamais.
4. **`textContent` uniquement côté frontend, jamais `innerHTML`.** Une réponse de modèle est du texte non fiable.
5. **Le message du visiteur n'est jamais concaténé aux instructions système** : il est passé comme donnée délimitée. Le modèle n'a aucun outil, aucune action, aucun accès réseau.
6. **Clé d'API côté serveur uniquement**, en variable d'environnement, jamais versionnée, jamais transmise au navigateur.
7. **Aucune conversation conservée**, ni serveur, ni navigateur. Journal technique limité aux métadonnées (statut, score, latence, jetons) — jamais le texte des questions.
8. **Le compte du fournisseur d'IA doit être établi dans l'EEE** (au nom de Manon, en France). Les conditions de Google prévoient que le contenu soumis à l'offre gratuite peut servir à améliorer ses produits, sauf pour un titulaire situé dans l'EEE / Suisse / Royaume-Uni, qui bénéficie des conditions de l'offre payante y compris sur le quota gratuit. C'est cette clause qui rend l'offre gratuite acceptable ici : elle n'est pas une formalité administrative.
9. **Plafond quotidien de consommation**, au-delà duquel le chatbot bascule en repli plutôt que de continuer à consommer.
10. **Les tests ne doivent jamais appeler un fournisseur réel.** Ils s'exécutent hors ligne, sans clé d'API, grâce à l'injection des adaptateurs.

### Modules attendus

| Module | Rôle |
|---|---|
| `app/routers/chat.py` | HTTP : limite de débit dédiée, validation d'entrée, codes de retour |
| `app/services/chat.py` | Orchestration : seuil, plafonds, replis |
| `app/repositories/knowledge.py` | Chargement de l'index, recherche — masque le moteur au reste |
| `app/services/embeddings.py` | Adaptateur embeddings, derrière une interface abstraite |
| `app/services/llm.py` | Adaptateur génération, derrière une interface abstraite |
| `app/security/sanitizer.py` | Validation d'entrée, détection des tentatives de détournement |
| `scripts/build_index.py` | Construction de l'index |
| `frontend/js/chat.js` | Widget, JS natif, chargé en différé |

### Tests spécifiques au RAG

Au-delà des tests habituels, un **jeu de questions de référence** (une vingtaine, avec le comportement attendu : répondue / hors périmètre) doit être exécuté à chaque modification. C'est le seul test qui protège la règle centrale dans la durée.

Prévoir également un jeu de messages de détournement, vérifiant que le comportement reste le refus.

### Prérequis bloquants avant indexation

- **Contenu définitif de la FAQ**, confirmé par Manon. Tant que ce n'est pas fait, l'index repose sur du contenu susceptible de changer.
- **Grille tarifaire** de Manon.
- **Politique de confidentialité** à compléter : Google (Gemini) devient un sous-traitant à déclarer, avec mention du transfert hors Union européenne, au même titre que Brevo, Google reCAPTCHA et Render.

## Projet de référence (`C:\labo\python\fastapi\14-douce-patte-claude-1`)

Un projet antérieur comparable existe, avec un chatbot RAG fonctionnel. **Il sert de référence architecturale, pas de source à copier.**

**À reprendre** : l'organisation en couches, l'injection des adaptateurs (qui rend les tests exécutables hors ligne), le prompt système défensif, le sanitizer avec journalisation des tentatives d'injection, la séparation du script d'indexation et de l'API, l'organisation des tests unitaires / intégration / fonctionnels.

**À ne pas reprendre :**

- **ChromaDB** — incompatible avec les contraintes d'hébergement (voir ci-dessus).
- **Le modèle d'embeddings local** — ne tient pas dans 512 Mo.
- **La persistance des demandes de contact en SQLite.** Le cahier des charges (§7) et la politique de confidentialité **publiée en ligne** affirment qu'aucune donnée personnelle n'est conservée côté serveur. Reprendre ce module mettrait le site en contradiction avec ce qu'il déclare publiquement.
- **La convention de dossier `src/`.** Ce dépôt est en production avec `backend/app/` ; ne pas renommer l'arborescence.
- **Son frontend** — hors périmètre (3 services sur 5, problèmes de contraste, polices déclarées mais non chargées). Seule la maquette validée fait foi.
- **Groq comme fournisseur** — remplacé par Gemini (fournisseur unique pour les deux rôles, embeddings inclus).

Son absence de seuil de pertinence est également un écart assumé : ici, le seuil est obligatoire.

## Direction visuelle (maquette validée)

- Couleurs : crème `#fff9ef`, encre `#38423f`, sauge `#bfd5c5`, sable `#f1e8dc`.
- Accent : brique douce `#bd4732` (~4,9:1 sur fond crème).
- Typographies : Nunito (texte courant), Petrona (titres), Google Fonts.
- Reproduire fidèlement la maquette — c'est elle qui fait foi.

### Widget de chat

- Ancrage **fixe, en bas à droite**, 24 px des bords (16 px sur mobile). Le panneau s'ouvre **au-dessus** de la bulle, qui reste visible et sert à refermer.
- Le widget consomme les **variables CSS du site** (`--coral`, `--ink`, `--sand`, `--sage`, `--surface`, `--muted`) : il suit la charte et le mode sombre automatiquement. Ne pas coder les couleurs en dur.
- Trois questions suggérées cliquables à l'ouverture.
- Réponse normale en vert sauge, question du visiteur en corail, réponse hors périmètre sur fond distinct avec étiquette « À confirmer avec Manon ».
- Indicateur de saisie (trois points), désactivé sous `prefers-reduced-motion`.
- Au-delà de quelques secondes d'attente, remplacer l'indicateur par un message explicite indiquant que le service se réveille, avec lien vers le formulaire.
- Mention permanente sous le champ de saisie : assistant automatisé, ne confirme ni disponibilité ni tarif, lien vers la politique de confidentialité.
- Présent sur les 8 pages, pages légales comprises.

## Points de vigilance

- Les 5 services sont tous présentés.
- Un bouton « Demander ce service » par service, pré-remplissant le champ « service souhaité ».
- Rédaction à la première personne (« je »), Manon exerce seule.
- Champ message du formulaire facultatif.
- Page FAQ : accordéon `<details>`/`<summary>`, réponses repliées par défaut, renvoi vers le formulaire en fin de page.
- Favicon, Open Graph et données structurées intégrés.

## Contenus à compléter avant mise en ligne

- **Photographies** : les images actuelles sont des images de banque, à remplacer par les photos de Manon.
- **Pages légales** : le SIRET (`000 000 000 00000`) et le téléphone (`06 05 05 05 05`) affichés dans les mentions légales sont **fictifs**. L'adresse et l'hébergeur restent également à compléter.
- **Contenu de la FAQ** : la page reprend les 11 questions/réponses de la maquette (secteur Paris 19e/20e, Les Lilas, Pantin, Bagnolet, rayon ~5 km ; tarifs indicatifs ; assurance ; délais ; engagement de nouvelles avec photo). **Une confirmation explicite de Manon reste attendue** — d'autant plus que ce contenu devient le corpus du chatbot. Ne pas le traiter comme définitif tant que l'arbitrage n'est pas clos.

## Commandes

```
# Backend (depuis backend/)
uvicorn app.main:app --reload --port 8123
pytest
ruff check . && pyright

# Index de connaissance (phase 2, depuis backend/)
python -m scripts.build_index

# Frontend (depuis frontend/)
npm run build
```

`frontend/dist/` et l'index de connaissance sont **versionnés** : Render ne les reconstruit pas. Les régénérer avant tout commit touchant au contenu ou aux fichiers statiques.

## Méthode

- Suivi des tâches en Kanban sur Trello.
- Git, dépôt GitHub sous le compte de Manon.
- Branches par tranche fonctionnelle (front + back ensemble), commits conventionnels avec portée : `feat(back):`, `fix(front):`.
- Ne rien pousser ni fusionner sans validation explicite de Yanis.
