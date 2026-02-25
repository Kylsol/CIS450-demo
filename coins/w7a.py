"""
Penny Detection Script using OpenCV
This script detects and counts copper-colored pennies in an image.
It uses HSV color space to distinguish pennies from silver coins.
"""

import cv2
import numpy as np

"""
Penny Detection Script using OpenCV
Detects and counts copper-colored pennies in `coins.png`.
Improvements in this version:
- stronger morphology to join broken copper regions
- contour filtering uses circularity (shape) and area
- radius computed via distance transform for more accurate fit
- fallback to minEnclosingCircle when needed
"""

import cv2
import numpy as np
import math


# ---- Parameters (tweakable) ----
IMAGE_PATH = "coins.png"
OUTPUT_PATH = "coins_detected.png"

# HSV copper range (tuned for typical penny color)
# these ranges can be adjusted if lighting differs
LOWER_COPPER1 = np.array([3, 70, 20])
UPPER_COPPER1 = np.array([32, 255, 255])
# small wrap-around range for very red-ish copper (optional)
LOWER_COPPER2 = np.array([170, 70, 20])
UPPER_COPPER2 = np.array([180, 255, 255])

# Morphology kernels
CLOSE_KERNEL = (7, 7)   # close holes inside coin regions
OPEN_KERNEL = (3, 3)      # remove small speckle noise

# Contour filters
MIN_AREA = 300       # lower area threshold (allows smaller coins)
MAX_AREA = 60000     # upper area threshold
MIN_CIRCULARITY = 0.35  # allow somewhat imperfect circles (occlusions)
MIN_RADIUS = 10
MAX_RADIUS = 200


def main():
    # Load image
    image = cv2.imread(IMAGE_PATH)
    if image is None:
        print(f"Error: Could not load image from {IMAGE_PATH}")
        return

    # Convert to HSV for color segmentation
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Build copper mask (combine ranges)
    mask1 = cv2.inRange(hsv, LOWER_COPPER1, UPPER_COPPER1)
    mask2 = cv2.inRange(hsv, LOWER_COPPER2, UPPER_COPPER2)
    copper_mask = cv2.bitwise_or(mask1, mask2)



    # Morphological operations to clean and join regions
    kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, CLOSE_KERNEL)
    kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, OPEN_KERNEL)

    kernel_dilate = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))

    # Close small holes inside coin region and then open to remove noise
    # copper_mask = cv2.morphologyEx(copper_mask, cv2.MORPH_CLOSE, kernel_close)
    # copper_mask = cv2.morphologyEx(copper_mask, cv2.MORPH_OPEN, kernel_open)
    copper_mask = cv2.morphologyEx(copper_mask, cv2.MORPH_CLOSE, kernel_close)
    # copper_mask = cv2.dilate(copper_mask, kernel_dilate, iterations=1)

    cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))

    # # --- Remove tiny specks using connected component area ---
    # num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(copper_mask, connectivity=8)

    # clean = np.zeros_like(copper_mask)
    # MIN_BLOB_AREA = 2000  # try 1500–4000

    # kept = 0
    # for i in range(1, num_labels):  # skip background label 0
    #     area = stats[i, cv2.CC_STAT_AREA]
    #     if area >= MIN_BLOB_AREA:
    #         clean[labels == i] = 255
    #         kept += 1

    # copper_mask = clean
    # print("Blobs kept after area filter:", kept)

    # # Save the FINAL mask you are actually using
    # cv2.imwrite("debug_copper_mask.png", copper_mask)
    # cv2.imwrite("debug_copper_preview.png", cv2.bitwise_and(image, image, mask=copper_mask))

    # --- Remove tiny specks using connected component area (relative threshold) ---
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(copper_mask, connectivity=8)

    areas = stats[1:, cv2.CC_STAT_AREA]  # skip background
    if len(areas) == 0:
        print("No copper blobs found at all (mask empty).")
        return

    max_area = int(areas.max())

    # Keep anything that's at least X% of the largest copper blob
    # (this avoids accidentally filtering out EVERYTHING)
    KEEP_RATIO = 0.15  # try 0.10–0.25
    min_keep_area = int(max_area * KEEP_RATIO)

    clean = np.zeros_like(copper_mask)
    kept = 0
    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        if area >= min_keep_area:
            clean[labels == i] = 255
            kept += 1

    copper_mask = clean
    print(f"Blobs kept: {kept} (max_area={max_area}, min_keep_area={min_keep_area})")

    # Save what you're actually using
    cv2.imwrite("debug_copper_mask.png", copper_mask)
    cv2.imwrite("debug_copper_preview.png", cv2.bitwise_and(image, image, mask=copper_mask))

    # # Slight blur helps Hough or distance transform be more stable
    # copper_mask = cv2.GaussianBlur(copper_mask, (7, 7), 0)
    # _, copper_mask = cv2.threshold(copper_mask, 127, 255, cv2.THRESH_BINARY)

    # Find contours on cleaned mask
    contours, _ = cv2.findContours(copper_mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    result = image.copy()
    penny_count = 0

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < MIN_AREA or area > MAX_AREA:
            continue

        perimeter = cv2.arcLength(cnt, True)
        if perimeter == 0:
            continue

        circularity = 4 * math.pi * (area / (perimeter * perimeter))
        if circularity < MIN_CIRCULARITY:
            # Not circular enough — skip small noise but allow slightly imperfect coins
            continue

        # Compute bounding box and create a mask for this contour only
        x, y, w, h = cv2.boundingRect(cnt)
        # add small padding to the crop
        pad = int(0.1 * max(w, h)) + 2
        x0 = max(x - pad, 0)
        y0 = max(y - pad, 0)
        x1 = min(x + w + pad, image.shape[1])
        y1 = min(y + h + pad, image.shape[0])

        # Crop the mask for the contour and compute distance transform
        crop_mask = np.zeros((y1 - y0, x1 - x0), dtype=np.uint8)
        # draw filled contour into the crop-local mask
        cnt_shifted = cnt - [x0, y0]
        cv2.drawContours(crop_mask, [cnt_shifted], -1, 255, -1)

        # Distance transform - distance to the nearest zero (background)
        dt = cv2.distanceTransform(crop_mask, cv2.DIST_L2, 5)
        minVal, maxVal, minLoc, maxLoc = cv2.minMaxLoc(dt)

        if maxVal >= 1.0:
            # center of inscribed circle in crop coordinates (col, row)
            center_local = (int(maxLoc[0]), int(maxLoc[1]))
            # convert to global image coordinates (x, y)
            center_global = (x0 + center_local[0], y0 + center_local[1])
            radius = int(maxVal)
            # slightly expand radius to better match outer coin boundary
            radius = int(radius * 1.15)
        else:
            # Fallback: use enclosing circle if distance transform fails
            (cx, cy), radius = cv2.minEnclosingCircle(cnt)
            center_global = (int(cx), int(cy))
            radius = int(radius)

        # Validate radius
        if radius < MIN_RADIUS or radius > MAX_RADIUS:
            continue

        # Draw a more accurate circle and a small center dot
        cv2.circle(result, center_global, radius, (0, 255, 0), 2)
        cv2.circle(result, center_global, 2, (0, 0, 255), -1)

        penny_count += 1

    # Save the annotated result image
    cv2.imwrite(OUTPUT_PATH, result)
    print(f"Result saved to {OUTPUT_PATH}")
    print(f"Number of pennies detected: {penny_count}")


if __name__ == '__main__':
    main()
