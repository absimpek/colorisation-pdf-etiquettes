# Microservice de colorisation PDF pour n8n

Ce mini-service reçoit un PDF en `POST /colorize-pdf`, applique un fond + encadré coloré, puis renvoie un PDF prêt à imprimer.

## Déploiement Render

1. Créer un repo GitHub.
2. Ajouter ces fichiers :
   - app.py
   - requirements.txt
   - render.yaml
3. Aller sur Render > New > Web Service.
4. Connecter le repo GitHub.
5. Render détecte `render.yaml`.
6. Déployer.
7. Récupérer l'URL Render, par exemple :
   https://colorisation-pdf-etiquettes.onrender.com

## URL à mettre dans n8n

Dans le node HTTP Request :

https://TON-URL-RENDER.onrender.com/colorize-pdf

## Test simple

Ouvrir dans le navigateur :

https://TON-URL-RENDER.onrender.com/health

Si la page affiche `OK`, le service est actif.
