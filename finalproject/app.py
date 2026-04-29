from flask import Flask, render_template, request, send_file
import os
import csv
import json
import zipfile
from io import StringIO
from collections import Counter
from pathlib import Path
from uuid import uuid4
from PIL import Image
from transformers import pipeline, BlipProcessor, BlipForConditionalGeneration
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from werkzeug.utils import secure_filename
from markupsafe import escape

try:
    import pytesseract
except ImportError:
    pytesseract = None

app = Flask(__name__)

UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "static/uploads")
EXPORT_FOLDER = os.environ.get("EXPORT_FOLDER", "static/exports")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["EXPORT_FOLDER"] = EXPORT_FOLDER
Path(UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)
Path(EXPORT_FOLDER).mkdir(parents=True, exist_ok=True)

# -----------------------------
# Lazy-loaded AI models
# -----------------------------
processor = None
caption_model = None
_detector = None


def load_models():
    """Load AI models only when needed so the app starts faster."""
    global processor, caption_model, _detector

    if processor is None:
        processor = BlipProcessor.from_pretrained(
            "Salesforce/blip-image-captioning-base"
        )
        caption_model = BlipForConditionalGeneration.from_pretrained(
            "Salesforce/blip-image-captioning-base"
        )
        _detector = pipeline(
            "object-detection",
            model="facebook/detr-resnet-50"
        )


# -----------------------------
# Image helpers
# -----------------------------
def draw_boxes(image_path, detections, output_path):
    image = Image.open(image_path).convert("RGB")

    fig, ax = plt.subplots(1, figsize=(10, 8))
    ax.imshow(image)

    for det in detections:
        box = det["box"]
        label = det["label"]
        score = det.get("score", 0)

        x = box["xmin"]
        y = box["ymin"]
        w = box["xmax"] - box["xmin"]
        h = box["ymax"] - box["ymin"]

        rect = patches.Rectangle(
            (x, y),
            w,
            h,
            linewidth=2,
            edgecolor="red",
            facecolor="none"
        )
        ax.add_patch(rect)

        ax.text(
            x,
            max(y - 5, 10),
            f"{label} ({score:.2f})",
            color="red",
            fontsize=10,
            backgroundcolor="white"
        )

    plt.axis("off")
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches="tight", pad_inches=0.1)
    plt.close()


def extract_color_palette(image: Image.Image, color_count: int = 5) -> list[str]:
    """Return a small brand/design-friendly color palette as HEX values."""
    small = image.convert("RGB")
    small.thumbnail((120, 120))

    paletted = small.convert("P", palette=Image.Palette.ADAPTIVE, colors=color_count)
    palette = paletted.getpalette() or []
    counts = paletted.getcolors() or []
    counts = sorted(counts, reverse=True)

    colors = []
    for _, palette_index in counts[:color_count]:
        base = palette_index * 3
        if base + 2 < len(palette):
            r, g, b = palette[base], palette[base + 1], palette[base + 2]
            colors.append(f"#{r:02x}{g:02x}{b:02x}")

    return colors


def extract_ocr_text(image: Image.Image) -> str:
    """Extract visible text if pytesseract and the Tesseract app are installed."""
    if pytesseract is None:
        return ""

    try:
        text = pytesseract.image_to_string(image)
    except Exception:
        return ""

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return " ".join(lines)[:500]


# -----------------------------
# Text helpers
# -----------------------------
def clean_sentence(text: str) -> str:
    if not text:
        return ""

    text = " ".join(text.strip().split())

    if not text:
        return ""

    text = text[0].upper() + text[1:]

    if text[-1] not in ".!?":
        text += "."

    return text


def remove_redundant_intro(text: str) -> str:
    text = clean_sentence(text)
    phrases = [
        "A picture of ",
        "An image of ",
        "A photo of ",
        "Picture of ",
        "Image of ",
        "Photo of ",
    ]

    for phrase in phrases:
        if text.lower().startswith(phrase.lower()):
            text = text[len(phrase):].strip()
            return clean_sentence(text)

    return text


def generate_tags_from_caption(caption: str, detected_summary: list[dict], ocr_text: str = "") -> list[str]:
    stop_words = {
        "a", "an", "the", "is", "are", "of", "on", "in", "at", "to",
        "for", "with", "and", "by", "this", "that", "as", "from", "it",
        "its", "into", "over", "under", "near", "next", "visible", "include",
        "includes", "context", "related", "image", "photo", "picture"
    }

    combined = f"{caption} {ocr_text}"
    for item in detected_summary:
        combined += f" {item['label']}"

    cleaned = combined.lower()
    for char in ",.!?:;()[]{}\"'":
        cleaned = cleaned.replace(char, " ")

    tags = []
    seen = set()
    for word in cleaned.split():
        word = word.strip("#")
        if word not in stop_words and len(word) > 2 and word not in seen:
            tags.append(word)
            seen.add(word)

    return tags[:12]


def format_detected_objects(detected_summary: list[dict]) -> str:
    objects = []

    for item in detected_summary:
        label = item["label"]
        count = item["count"]

        if count == 1:
            objects.append(f"one {label}")
        else:
            objects.append(f"{count} {label}s")

    if not objects:
        return ""

    if len(objects) == 1:
        return objects[0]

    return ", ".join(objects[:-1]) + f", and {objects[-1]}"


def confidence_summary(detection_details: list[dict]) -> dict:
    if not detection_details:
        return {
            "label": "No objects detected",
            "score": None,
            "message": "No object detections passed the selected confidence threshold."
        }

    avg = sum(item["score"] for item in detection_details) / len(detection_details)

    if avg >= 0.80:
        label = "High confidence"
        message = "Detected objects look reliable."
    elif avg >= 0.65:
        label = "Medium confidence"
        message = "Detected objects look usable, but should still be reviewed."
    else:
        label = "Low confidence"
        message = "Some detected objects may be uncertain, so review before publishing."

    return {
        "label": label,
        "score": round(avg, 2),
        "message": message
    }


def refine_caption(raw_caption: str, detected_summary: list[dict], context: str = "", ocr_text: str = "") -> str:
    caption = remove_redundant_intro(raw_caption)

    if not caption:
        caption = "Generated caption for the uploaded image."

    labels = [item["label"] for item in detected_summary]
    missing_labels = [label for label in labels if label.lower() not in caption.lower()]

    if missing_labels:
        caption += f" Detected elements include {', '.join(missing_labels[:4])}."

    if ocr_text:
        short_text = ocr_text[:120]
        caption += f" Visible text reads: {short_text}."

    if context:
        caption += f" Related page context: {context.strip()}."

    return " ".join(caption.split())


def generate_alt_text(raw_caption: str, detected_summary: list[dict], context: str = "", ocr_text: str = "") -> str:
    alt_text = remove_redundant_intro(raw_caption)

    if not alt_text:
        alt_text = "Visual content detected in the uploaded image."

    detected_objects = format_detected_objects(detected_summary)
    if detected_objects:
        alt_text += f" Visible elements include {detected_objects}."

    if ocr_text:
        alt_text += f" Text in image: {ocr_text[:120]}."

    if context:
        alt_text += f" Context: {context.strip()}."

    return " ".join(alt_text.split())


def build_html_snippet(image_path: str, alt_text: str, caption: str, tags: list[str]) -> str:
    tag_string = ", ".join(tags)

    return f'''<figure class="ai-caption-card">
  <img src="/static/{escape(image_path)}" alt="{escape(alt_text)}">
  <figcaption>{escape(caption)}</figcaption>
  <meta name="keywords" content="{escape(tag_string)}">
</figure>'''


def build_markdown_snippet(image_path: str, alt_text: str) -> str:
    return f"![{alt_text}](/static/{image_path})"


def build_json_ld(image_path: str, alt_text: str, caption: str, tags: list[str]) -> str:
    data = {
        "@context": "https://schema.org",
        "@type": "ImageObject",
        "contentUrl": f"/static/{image_path}",
        "caption": caption,
        "description": alt_text,
        "keywords": tags,
    }
    return json.dumps(data, indent=2)


def quality_checks(alt_text: str, detection_details: list[dict], threshold: float, ocr_text: str) -> list[dict]:
    checks = []
    lower_alt = alt_text.lower()

    if not alt_text.strip():
        checks.append({"type": "warning", "message": "Alt text is empty."})

    if len(alt_text) > 180:
        checks.append({"type": "warning", "message": "Alt text is longer than 180 characters. Consider shortening it."})

    if lower_alt.startswith(("image of", "picture of", "photo of", "an image of", "a picture of", "a photo of")):
        checks.append({"type": "tip", "message": "Avoid starting alt text with 'image of', 'picture of', or 'photo of'."})

    if detection_details:
        low_confidence = [
            item for item in detection_details
            if item["score"] < max(threshold + 0.10, 0.65)
        ]
        if low_confidence:
            checks.append({"type": "tip", "message": "Some detected objects have lower confidence, so review the wording before using it."})

    if ocr_text and ocr_text[:60].lower() not in lower_alt:
        checks.append({"type": "tip", "message": "OCR found text in the image. Make sure important visible text is included in the alt text."})

    if not checks:
        checks.append({"type": "success", "message": "Alt text looks reasonable."})

    return checks


def build_csv(results: list[dict]) -> str:
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "filename",
        "caption",
        "alt_text",
        "tags",
        "detected_objects",
        "confidence",
        "ocr_text",
        "colors",
        "html",
        "markdown",
        "json_ld"
    ])

    for result in results:
        writer.writerow([
            result["filename"],
            result["caption"],
            result["alt_text"],
            ", ".join(result["tags"]),
            ", ".join(
                f'{item["count"]} {item["label"]}'
                for item in result["detected_summary"]
            ),
            result["confidence"]["label"],
            result["ocr_text"],
            ", ".join(result["colors"]),
            result["html_snippet"],
            result["markdown_snippet"],
            result["json_ld"]
        ])

    return output.getvalue()


def build_zip(results: list[dict], csv_export: str) -> str:
    export_id = uuid4().hex[:10]
    zip_filename = f"caption_export_{export_id}.zip"
    zip_path = os.path.join(app.config["EXPORT_FOLDER"], zip_filename)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("captions.csv", csv_export)

        for result in results:
            base_name = Path(result["filename"]).stem
            zip_file.writestr(f"html/{base_name}.html", result["html_snippet"])
            zip_file.writestr(f"markdown/{base_name}.md", result["markdown_snippet"])
            zip_file.writestr(f"json_ld/{base_name}.json", result["json_ld"])

    return f"exports/{zip_filename}"


@app.route("/healthz", methods=["GET"])
def healthz():
    return {"status": "ok"}, 200


@app.route("/download/<path:filename>", methods=["GET"])
def download_export(filename):
    safe_name = secure_filename(filename)
    file_path = os.path.join(app.config["EXPORT_FOLDER"], safe_name)

    if not os.path.exists(file_path):
        return "Export not found", 404

    return send_file(file_path, as_attachment=True)


# -----------------------------
# Main route
# -----------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    results = []
    error = None
    threshold = 0.3
    context = ""
    csv_export = ""
    zip_export = ""
    ocr_available = pytesseract is not None

    if request.method == "POST":
        load_models()

        files = request.files.getlist("image")
        threshold_raw = request.form.get("threshold", "0.3")
        context = request.form.get("context", "").strip()
        enable_ocr = request.form.get("enable_ocr") == "on"

        try:
            threshold = float(threshold_raw)
        except ValueError:
            threshold = 0.3

        threshold = max(0.0, min(threshold, 1.0))

        for file in files:
            if not file or not file.filename:
                continue

            safe_name = secure_filename(file.filename)
            if not safe_name:
                continue

            unique_prefix = uuid4().hex[:8]
            unique_name = f"{unique_prefix}_{safe_name}"
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
            file.save(filepath)

            try:
                image = Image.open(filepath).convert("RGB")

                # Caption generation (BLIP)
                inputs = processor(images=image, return_tensors="pt")
                out = caption_model.generate(**inputs, max_new_tokens=50)
                raw_caption = processor.decode(out[0], skip_special_tokens=True)

                # Object detection (DETR)
                detections = _detector(image)
                filtered_detections = [
                    det for det in detections if det.get("score", 0) >= threshold
                ]

                boxed_image = None
                detected_summary = []
                detection_details = []

                if filtered_detections:
                    boxed_filename = f"boxed_{unique_name}"
                    boxed_path = os.path.join(app.config["UPLOAD_FOLDER"], boxed_filename)
                    draw_boxes(filepath, filtered_detections, boxed_path)
                    boxed_image = f"uploads/{boxed_filename}"

                    label_counts = Counter(det["label"] for det in filtered_detections)
                    detected_summary = [
                        {"label": label, "count": count}
                        for label, count in sorted(label_counts.items())
                    ]

                    detection_details = sorted(
                        [
                            {
                                "label": det["label"],
                                "score": round(float(det.get("score", 0)), 2)
                            }
                            for det in filtered_detections
                        ],
                        key=lambda x: x["score"],
                        reverse=True
                    )

                ocr_text = extract_ocr_text(image) if enable_ocr else ""
                colors = extract_color_palette(image)
                caption = refine_caption(raw_caption, detected_summary, context, ocr_text)
                alt_text = generate_alt_text(raw_caption, detected_summary, context, ocr_text)
                tags = generate_tags_from_caption(caption, detected_summary, ocr_text)
                image_path = f"uploads/{unique_name}"
                html_snippet = build_html_snippet(image_path, alt_text, caption, tags)
                markdown_snippet = build_markdown_snippet(image_path, alt_text)
                json_ld = build_json_ld(image_path, alt_text, caption, tags)
                checks = quality_checks(alt_text, detection_details, threshold, ocr_text)
                confidence = confidence_summary(detection_details)

                results.append({
                    "filename": safe_name,
                    "image_path": image_path,
                    "boxed_image": boxed_image,
                    "caption": caption,
                    "raw_caption": clean_sentence(raw_caption),
                    "tags": tags,
                    "detected_summary": detected_summary,
                    "detection_details": detection_details,
                    "confidence": confidence,
                    "alt_text": alt_text,
                    "ocr_text": ocr_text,
                    "ocr_enabled": enable_ocr,
                    "colors": colors,
                    "html_snippet": html_snippet,
                    "markdown_snippet": markdown_snippet,
                    "json_ld": json_ld,
                    "checks": checks
                })

            except Exception as e:
                error = f"Error processing {safe_name}: {str(e)}"

        if results:
            csv_export = build_csv(results)
            zip_export = build_zip(results, csv_export)

    return render_template(
        "index.html",
        results=results,
        error=error,
        threshold=threshold,
        context=context,
        csv_export=csv_export,
        zip_export=zip_export,
        ocr_available=ocr_available
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=True)
