from flask import Flask, request, send_file, jsonify
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color
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
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=(width, height))

    red = r / 255
    green = g / 255
    blue = b / 255

    # Calque couleur par-dessus le PDF, mais très transparent
    c.setFillColor(Color(red, green, blue, alpha=0.18))
    c.rect(0, 0, width, height, fill=1, stroke=0)

    # Encadré coloré visible
    c.setStrokeColor(Color(red, green, blue, alpha=1))
    c.setLineWidth(8)
    margin = 8
    c.rect(margin, margin, width - (margin * 2), height - (margin * 2), fill=0, stroke=1)

    c.save()
    packet.seek(0)
    return PdfReader(packet).pages[0]

@app.route("/colorize-pdf", methods=["POST"])
def colorize_pdf():
    if "file" not in request.files:
        return jsonify({"error": "Aucun fichier reçu. Le champ form-data doit s'appeler file."}), 400

    uploaded_file = request.files["file"]

    try:
        r = int(request.form.get("r", 217))
        g = int(request.form.get("g", 217))
        b = int(request.form.get("b", 217))
    except ValueError:
        return jsonify({"error": "Les valeurs r, g, b doivent être des nombres."}), 400

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
            # On garde la page originale, puis on fusionne le calque couleur par-dessus.
            # L'ancienne version faisait l'inverse, donc la couleur passait derrière le fond blanc.
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
        return jsonify({"error": str(e)}), 500

    finally:
        try:
            os.unlink(input_tmp.name)
        except Exception:
            pass

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
