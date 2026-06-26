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
    Crée un voile coloré AU-DESSUS du PDF.
    Version renforcée pour que le rendu soit bien visible même sur fond blanc.
    """

    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=(width, height))

    red = r / 255
    green = g / 255
    blue = b / 255

    # Plus la couleur est claire, plus on augmente l'opacité.
    brightness = (r + g + b) / 3

    if brightness > 230:
        fill_alpha = 0.70
    else:
        fill_alpha = 0.50

    # Voile coloré visible par-dessus la page
    c.saveState()
    c.setFillColorRGB(red, green, blue)
    c.setFillAlpha(fill_alpha)
    c.rect(0, 0, width, height, fill=1, stroke=0)
    c.restoreState()

    # Encadré coloré bien marqué
    c.saveState()
    c.setStrokeColorRGB(red, green, blue)
    c.setStrokeAlpha(1)
    c.setLineWidth(14)
    margin = 8
    c.rect(margin, margin, width - (margin * 2), height - (margin * 2), fill=0, stroke=1)
    c.restoreState()

    c.save()
    packet.seek(0)

    return PdfReader(packet).pages[0]


@app.route("/colorize-pdf", methods=["POST"])
def colorize_pdf():
    """
    Endpoint appelé par n8n.
    Attend un body form-data avec :
    - file : PDF
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
        r = int(request.form.get("r", 211))
        g = int(request.form.get("g", 211))
        b = int(request.form.get("b", 211))
    except ValueError:
        return jsonify({
            "error": "Les valeurs r, g, b doivent être des nombres entre 0 et 255."
        }), 400

    # Si n8n envoie le gris trop clair #F0F0F0, on le force en #D3D3D3,
    # sinon sur une page blanche il paraît quasiment invisible.
    if r >= 235 and g >= 235 and b >= 235:
        r, g, b = 211, 211, 211

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

            # Le calque est fusionné par-dessus la page originale
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
