from flask import Flask, request, send_file, jsonify
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
import tempfile
import os
import io

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "ok",
        "message": "Microservice colorisation PDF actif",
        "endpoint": "/colorize-pdf",
        "method": "POST"
    })


def create_overlay(width, height, r, g, b):
    """
    Crée un calque PDF transparent qui sera posé PAR-DESSUS la page originale.
    Important : on utilise setFillAlpha / setStrokeAlpha pour forcer la vraie transparence.
    """

    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=(width, height))

    red = r / 255
    green = g / 255
    blue = b / 255

    # Voile coloré par-dessus le PDF.
    # Augmente 0.30 à 0.35 ou 0.40 si tu veux une couleur plus visible.
    c.saveState()
    c.setFillColorRGB(red, green, blue)
    c.setFillAlpha(0.30)
    c.rect(0, 0, width, height, fill=1, stroke=0)
    c.restoreState()

    # Encadré coloré autour de la page.
    c.saveState()
    c.setStrokeColorRGB(red, green, blue)
    c.setStrokeAlpha(0.95)
    c.setLineWidth(10)
    margin = 8
    c.rect(
        margin,
        margin,
        width - (margin * 2),
        height - (margin * 2),
        fill=0,
        stroke=1
    )
    c.restoreState()

    c.save()
    packet.seek(0)

    return PdfReader(packet).pages[0]


@app.route("/colorize-pdf", methods=["POST"])
def colorize_pdf():
    """
    Endpoint appelé par n8n.
    Attend un body form-data avec :
    - file : le PDF
    - r : rouge 0-255
    - g : vert 0-255
    - b : bleu 0-255
    """

    if "file" not in request.files:
        return jsonify({
            "error": "Aucun fichier reçu. Le champ form-data doit s'appeler file."
        }), 400

    uploaded_file = request.files["file"]

    try:
        r = int(request.form.get("r", 217))
        g = int(request.form.get("g", 217))
        b = int(request.form.get("b", 217))
    except ValueError:
        return jsonify({
            "error": "Les valeurs r, g, b doivent être des nombres entre 0 et 255."
        }), 400

    for value, name in [(r, "r"), (g, "g"), (b, "b")]:
        if value < 0 or value > 255:
            return jsonify({
                "error": f"La valeur {name} doit être comprise entre 0 et 255."
            }), 400

    input_tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    output_tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")

    try:
        uploaded_file.save(input_tmp.name)

        reader = PdfReader(input_tmp.name)
        writer = PdfWriter()

        for page in reader.pages:
            width = float(page.mediabox.width)
            height = float(page.mediabox.height)

            overlay = create_overlay(width, height, r, g, b)

            # IMPORTANT :
            # On fusionne le calque couleur SUR la page originale.
            # Donc le filtre coloré passe bien devant le fond blanc du PDF.
            page.merge_page(overlay)

            writer.add_page(page)

        with open(output_tmp.name, "wb") as f:
            writer.write(f)

        return send_file(
            output_tmp.name,
            mimetype="application/pdf",
            as_attachment=True,
            download_name="etiquettes_colorees.pdf"
        )

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

    finally:
        try:
            os.unlink(input_tmp.name)
        except Exception:
            pass


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
