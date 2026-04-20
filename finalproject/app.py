from flask import Flask, render_template, request
import os
from collections import Counter
from PIL import Image
from transformers import pipeline, BlipProcessor, BlipForConditionalGeneration
import torch

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.patches as patches

app = Flask(__name__)

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# -----------------------------
# Lazy-loaded AI models (safer for deployment)
# -----------------------------
processor = None
caption_model = None
detector = None

def load_models():
    global processor, caption_model, detector

    if processor is None:
        processor = BlipProcessor.from_pretrained(
            "Salesforce/blip-image-captioning-large"
        )
        caption_model = BlipForConditionalGeneration.from_pretrained(
            "Salesforce/blip-image-captioning-large"
        )
        detector = pipeline(
            "object-detection",
            model="facebook/detr-resnet-50"
        )

# -----------------------------
# Draw bounding boxes
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

# -----------------------------
# Generate tags from caption
# -----------------------------
def generate_tags_from_caption(caption: str) -> list[str]:
    stop_words = {
        "a", "an", "the", "is", "are", "of", "on", "in", "at", "to",
        "for", "with", "and", "by", "this", "that"
    }

    words = caption.lower().replace(",", "").replace(".", "").split()

    tags = []
    seen = set()

    for word in words:
        if word not in stop_words and len(word) > 2 and word not in seen:
            tags.append(word)
            seen.add(word)

    return tags[:8]

# -----------------------------
# Generate alt text
# -----------------------------
def generate_alt_text(caption: str, detected_summary: list[dict]) -> str:
    if caption:
        alt_text = caption.strip().capitalize()
    else:
        alt_text = "An image"

    if detected_summary:
        objects = []
        for item in detected_summary:
            label = item["label"]
            count = item["count"]

            if count == 1:
                objects.append(f"one {label}")
            else:
                objects.append(f"{count} {label}s")

        alt_text += f". Contains {', '.join(objects)}"

    return alt_text

# -----------------------------
# Main route
# -----------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    load_models()  # ensure models are loaded only when needed

    results = []
    error = None
    threshold = 0.5

    if request.method == "POST":
        files = request.files.getlist("image")
        threshold_raw = request.form.get("threshold", "0.5")

        try:
            threshold = float(threshold_raw)
        except ValueError:
            threshold = 0.5

        threshold = max(0.0, min(threshold, 1.0))

        for file in files:
            if not file or not file.filename:
                continue

            filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
            file.save(filepath)

            try:
                image = Image.open(filepath).convert("RGB")

                # -----------------------------
                # Caption generation (BLIP)
                # -----------------------------
                inputs = processor(images=image, return_tensors="pt")
                out = caption_model.generate(**inputs, max_new_tokens=50)
                caption = processor.decode(out[0], skip_special_tokens=True)

                tags = generate_tags_from_caption(caption) if caption else []

                # -----------------------------
                # Object detection (DETR)
                # -----------------------------
                detections = detector(image)
                filtered_detections = [
                    det for det in detections if det.get("score", 0) >= threshold
                ]

                boxed_image = None
                detected_summary = []
                detection_details = []

                if filtered_detections:
                    boxed_filename = f"boxed_{file.filename}"
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

                alt_text = generate_alt_text(caption, detected_summary)

                results.append({
                    "image_path": f"uploads/{file.filename}",
                    "boxed_image": boxed_image,
                    "caption": caption,
                    "tags": tags,
                    "detected_summary": detected_summary,
                    "detection_details": detection_details,
                    "alt_text": alt_text
                })

            except Exception as e:
                error = f"Error processing {file.filename}: {str(e)}"

    return render_template(
        "index.html",
        results=results,
        error=error,
        threshold=threshold
    )

# -----------------------------
# ENTRY POINT (RENDER SAFE)
# -----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)