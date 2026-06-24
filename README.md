# Microservice Render - Colorisation PDF étiquettes

Version légère sans PyMuPDF, compatible Render Free.

## Fichiers

- app.py
- requirements.txt
- render.yaml

## Déploiement

Sur Render :
- Build Command : pip install -r requirements.txt
- Start Command : gunicorn app:app

## URL n8n

Dans le node HTTP Request :

https://TON-SERVICE.onrender.com/colorize-pdf

## Body form-data

- file : fichier PDF binaire
- r : valeur rouge, ex 167
- g : valeur verte, ex 199
- b : valeur bleue, ex 231
