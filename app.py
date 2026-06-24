from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import fitz  # PyMuPDF
import tempfile
import os

app = Flask(__name__)
CORS(app)

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "ok",
        "message": "Microservice de colorisation PDF actif",
        "endpoint": "/colorize-pdf",
        "method": "POST"
    })

@app.route("/health", methods=["GET"])
def health():
    return "OK", 200

@app.route("/colorize-pdf", methods=["POST"])
def colorize_pdf():
    if "file" not in request.files:
        return jsonify({"error": "Aucun fichier reçu. Le champ form-data doit s'appeler 'file'."}), 400

    uploaded_file = request.files["file"]

    try:
        r = int(request.form.get("r", 217))
        g = int(request.form.get("g", 217))
        b = int(request.form.get("b", 217))
    except ValueError:
        return jsonify({"error": "Les valeurs r, g, b doivent être des nombres."}), 400

    # Sécurité simple
    r = max(0, min(255, r))
    g = max(0, min(255, g))
    b = max(0, min(255, b))

    color = (r / 255, g / 255, b / 255)

    input_tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    output_tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")

    try:
        uploaded_file.save(input_tmp.name)

        pdf = fitz.open(input_tmp.name)

        for page in pdf:
            rect = page.rect

            # Fond léger semi-transparent
            page.draw_rect(
                rect,
                color=None,
                fill=color,
                overlay=True,
                fill_opacity=0.22
            )

            # Encadré coloré visible
            margin = 8
            border_rect = fitz.Rect(
                rect.x0 + margin,
                rect.y0 + margin,
                rect.x1 - margin,
                rect.y1 - margin
            )

            page.draw_rect(
                border_rect,
                color=color,
                width=6,
                overlay=True
            )

        pdf.save(output_tmp.name, garbage=4, deflate=True)
        pdf.close()

        day = request.form.get("day", "jour")
        download_name = f"etiquettes_{day}_colorees.pdf".replace(" ", "_")

        return send_file(
            output_tmp.name,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=download_name
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        try:
            os.remove(input_tmp.name)
        except Exception:
            pass
        # Ne pas supprimer output_tmp avant send_file dans certains environnements WSGI.
