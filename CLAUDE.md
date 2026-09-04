# Douce Patte — Site vitrine

Site vitrine pour Manon Dubois, auto-entrepreneuse en garde et promenade d'animaux (chiens et chats). Développé par Yanis Belkacem (prestataire).

Ce dossier (`6-developpement-et-tests`) contient le code du site. Les documents de cadrage sont dans les dossiers voisins du même projet local (`..\`) :

- `..\2-cahier-des-charges\2b-rédaction-du-cahier-des-charges.docx` — périmètre contractuel, signé (v1.3)
- `..\3-specifications-fonctionnelles\3a-specifications-fonctionnelles.docx` — comportement attendu, en user stories (v1.2)
- `..\4-conception-ux-ui\4a-maquette-dapres-le-code.html` — maquette visuelle validée par la cliente (v5.0)
- `..\5-specifications-techniques\5a-specifications-techniques.md` — choix d'implémentation (v2.2)

**Toujours se référer à ces documents avant de trancher un point de comportement, de contenu ou de design.** Ne pas réinterpréter le périmètre ni ajouter de fonctionnalité qui n'y figure pas.

## Résumé du projet

- 5 services : promenade de chiens, visites à domicile pour chats, garde pendant les vacances, passage nourriture/eau, garde ponctuelle en journée.
- 7 pages : Accueil, Services, À propos, Contact, Mentions légales, Politique de confidentialité, Cookies.
- Formulaire de contact : nom, email, téléphone, service souhaité (obligatoires), message (facultatif) → email de notification à Manon, aucune donnée stockée en base.
- Pas de compte utilisateur, pas de CRM, pas de widget de chat.
- Domaine : `douce-patte.fr` (réservé). Hébergement : Render. Dépôt : GitHub, sous le compte de Manon.

## Stack technique

- **Frontend** : HTML / CSS / JS natifs, sans framework. Animations avec GSAP (chargée en `defer`, respecte `prefers-reduced-motion`).
- **Backend** : Python 3.12+, FastAPI, validation avec Pydantic. Un seul endpoint métier (`POST /contact`).
- **Base de données** : aucune.
- **Anti-spam du formulaire** : honeypot + Google reCAPTCHA v3 (invisible).
- **Email** : Mailtrap en développement/test, Brevo en production (société française, données hébergées en France).
- **Build** : esbuild (JS) et Lightning CSS, pour la minification des fichiers statiques.
- **Tests** : pytest (unitaires + intégration via le TestClient FastAPI), Playwright (parcours fonctionnel du formulaire), pytest-cov pour la couverture.
- **Analyse statique** : Ruff + Pyright (Python), validateur W3C + Stylelint + ESLint (frontend).
- **Déploiement** : Render, manuel pour l'instant (pas de CI/CD).

Détail complet et schéma de flux du formulaire : `5-specifications-techniques\5a-specifications-techniques.md`.

## Point de départ du code

**Développement repris de zéro dans ce dossier.** Il existe un frontend de référence (`C:\labo\python\fastapi\14-douce-patte-claude-1`) dont la maquette validée s'est inspirée, mais **ne pas copier ses fichiers ni partir de son code** : il contient des éléments hors périmètre (widget de chat), des incohérences (3 services affichés sur 5), des problèmes de contraste, et des polices déclarées mais jamais chargées. La seule référence à suivre est la maquette validée (§ ci-dessus) et ce document.

## Direction visuelle (maquette validée)

- Couleurs : crème `#fff9ef`, encre `#38423f`, sauge `#bfd5c5`, sable `#f1e8dc`.
- Couleur d'accent : brique douce `#bd4732` (remplace le corail `#c6462a` de la maquette d'origine, trop proche du terracotta de la charte Anthropic/Claude — même famille de teinte, mais plus sombre et saturée que Claude tout en restant moins intense qu'un rouge-brique pur ; décision prise en cours de développement, après passage par un ambre, un vert forêt et une brique plus soutenue).
- Typographies : Nunito (texte courant), Petrona (titres), chargées depuis Google Fonts.
- Composants et mise en page : reproduire fidèlement la maquette (`4a-maquette-dapres-le-code.html`) — c'est elle qui fait foi, pas le frontend de référence.

## Points de vigilance repris de la maquette

- Les 5 services sont tous présentés.
- Un bouton « Demander ce service » par service, pré-remplissant le champ « service souhaité » du formulaire de contact.
- Pas de widget de chat.
- Rédaction à la première personne (« je »), Manon exerce seule.
- Contraste de l'accent : `#bd4732` (~4,9:1 sur fond crème), pour rester accessible.
- Champ message du formulaire facultatif.
- Favicon, Open Graph et données structurées à intégrer — balises prêtes dans la maquette, page « Identité & partage ».

## Photographies

Les 6 photos actuellement dans la maquette sont des images de banque, à remplacer par les photos définitives de Manon avant mise en ligne (portrait d'elle, scènes avec les animaux, dont une scène de repas/gamelle). Prévoir un point de blocage explicite dans le planning tant que ces photos ne sont pas fournies.

## Pages légales

Les pages Mentions légales, Politique de confidentialité et Cookies de la maquette contiennent des champs entre crochets (SIRET, adresse professionnelle, hébergeur, durée de conservation) : à compléter avec les informations réelles de Manon avant mise en ligne, pas avant.

## Méthode

- Suivi des tâches en Kanban sur Trello.
- Versionning Git, dépôt GitHub sous le compte de Manon.
