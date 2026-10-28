# KAYSEUR MDX — Bot Telegram

## Déploiement
1. Pousse ce dossier sur GitHub (`.env` et `data.json` sont ignorés).
2. Sur l'hébergeur : commande de démarrage `python bot.py` (ou utilise le `Dockerfile`).
3. Ajoute les variables de `.env.example` dans les "Environment variables" de l'hébergeur.
4. Ajoute le bot en **admin** de ta chaîne et de ton groupe (abonnement obligatoire),
   et en **admin avec droits "supprimer les messages" + "restreindre les membres"**
   dans chaque groupe où tu veux l'anti-liens.

## Images (dossier assets/)
- `menu.jpg`    → image du /menu
- `welcome.jpg` → image de bienvenue
- `goodbye.jpg` → image d'au revoir
- `menu.mp3`    → (optionnel) musique envoyée après /menu. Sans ce fichier, le bot
  la télécharge via yt-dlp avec la recherche `MENU_MUSIC_QUERY`.

## Ajouter des commandes
- Textes aléatoires : ajoute une entrée dans `TEXTS`.
- Quiz : ajoute des questions / une catégorie dans `QUIZ`.
- Autre : fonction avec `@cmd("nom", "Catégorie", "description")`.
