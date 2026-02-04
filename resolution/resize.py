import cv2 as cv
import os

PHOTO_DIR = "../photos"
OUTPUT_DIR = "."

TARGET_WIDTH = 640

for filename in os.listdir(PHOTO_DIR):
    if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
        continue

    input_path = os.path.join(PHOTO_DIR, filename)
    img = cv.imread(input_path)

    if img is None:
        print(f"Could not read: {filename}")
        continue

    height, width , channels = img.shape

    scale = width / TARGET_WIDTH
    new_height = round(height / scale)

    resized = cv.resize(
        img, 
        (TARGET_WIDTH, new_height),
        interpolation=cv.INTER_LINEAR
    )

    name, ext = os.path.splitext(filename)
    output_name = f"{name}-640x{new_height}.png"
    output_path = os.path.join(OUTPUT_DIR, output_name)

    cv.imwrite(output_path, resized)
    print(f"Saved {output_name}")
