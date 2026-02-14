#!/usr/bin/env python3
"""
Create a panorama using OpenCV's high-level Stitcher API.

Run (from the panorama directory):
  python panorama.py panorama ../resolution/*.png
Outputs:
  result.jpg (in the panorama directory)
"""

import sys
import glob
import cv2 as cv
import numpy as np



def expand_inputs(args):
    """Expand any wildcard patterns (globs) into concrete file paths."""
    paths = []
    for a in args:
        # Expand wildcards like ../resolution/*.png
        matches = glob.glob(a)
        if matches:
            paths.extend(matches)
        else:
            paths.append(a)
    # Keep a stable order (important for panoramas)
    return sorted(paths)

def stitch_once(images, mode):
    stitcher = cv.Stitcher_create(mode)
    return stitcher.stitch(images)


def hierarchical_stitch(imgs, mode, group_size=3):
    stitched = []

    # Step 1: stitch small groups
    for i in range(0, len(imgs), group_size):
        group = imgs[i:i+group_size]
        if len(group) == 1:
            stitched.append(group[0])
            continue

        status, pano = stitch_once(group, mode)
        print(f"Group {i//group_size} size={len(group)} status={status}")

        if status == cv.Stitcher_OK and pano is not None:
            stitched.append(pano)
        else:
            stitched.extend(group)

    # Step 2: stitch merged results
    if len(stitched) < 2:
        return cv.Stitcher_ERR_NEED_MORE_IMGS, None

    status, pano = stitch_once(stitched, mode)
    print(f"Final merge chunks={len(stitched)} status={status}")
    return status, pano


def main():
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python panorama.py panorama <images...>")
        print("Example:")
        print("  python panorama.py panorama ../resolution/*.png")
        sys.exit(1)

    mode_arg = sys.argv[1].lower()
    if mode_arg not in ("panorama", "scans"):
        print("Mode must be 'panorama' or 'scans'")
        sys.exit(1)

    mode = cv.Stitcher_PANORAMA if mode_arg == "panorama" else cv.Stitcher_SCANS

    image_args = sys.argv[2:]
    image_paths = expand_inputs(image_args)

    if len(image_paths) < 2:
        print("Need at least 2 images.")
        print("Got:", image_paths)
        sys.exit(1)

    # Load images
    imgs = []
    for p in image_paths:
        img = cv.imread(p)
        if img is None:
            print("Could not read:", p)
            sys.exit(1)
        imgs.append(img)

    # Stitch
    stitcher = cv.Stitcher_create(mode)

    # Try lowering the pano confidence threshold (default is often ~1.0)
    if hasattr(stitcher, "setPanoConfidenceThresh"):
        stitcher.setPanoConfidenceThresh(0.5)   # try 0.3, 0.5, 0.8
        print("Set pano confidence threshold to 0.5")
    else:
        print("This OpenCV build doesn't expose setPanoConfidenceThresh()")

    status, pano = stitcher.stitch(imgs)

    if status != cv.Stitcher_OK:
        print("Stitching failed. OpenCV status code:", status)
        sys.exit(1)

    # --- Crop black borders (robust flood-fill; fixes top/bottom not cropping) ---
    import numpy as np  # make sure this is at the top of your file with other imports

    gray = cv.cvtColor(pano, cv.COLOR_BGR2GRAY)

    # Treat near-black as background (raise to 15/20 if needed)
    _, mask = cv.threshold(gray, 10, 255, cv.THRESH_BINARY)

    # Clean small specks so they don't prevent cropping
    kernel = cv.getStructuringElement(cv.MORPH_RECT, (9, 9))
    mask = cv.morphologyEx(mask, cv.MORPH_OPEN, kernel)
    mask = cv.morphologyEx(mask, cv.MORPH_CLOSE, kernel)

    # Flood-fill background from corners
    h, w = mask.shape[:2]
    ff = cv.copyMakeBorder(mask, 1, 1, 1, 1, cv.BORDER_CONSTANT, value=0)

    # floodFill requires a separate mask of size (H+2, W+2) for the image being flood-filled
    flood_mask = np.zeros((h + 4, w + 4), dtype=np.uint8)

    cv.floodFill(ff, flood_mask, (0, 0), 255)
    cv.floodFill(ff, flood_mask, (w + 1, 0), 255)
    cv.floodFill(ff, flood_mask, (0, h + 1), 255)
    cv.floodFill(ff, flood_mask, (w + 1, h + 1), 255)

    # Background is now 255; invert to get content
    ff = ff[1:-1, 1:-1]  # remove border
    content = cv.bitwise_not(ff)

    ys, xs = np.where(content > 0)
    if len(xs) and len(ys):
        x0, x1 = xs.min(), xs.max()
        y0, y1 = ys.min(), ys.max()
        pano = pano[y0:y1+1, x0:x1+1]

    # Save result
    out_file = "result.jpg"
    cv.imwrite(out_file, pano)
    print("✅ Panorama saved as:", out_file)

if __name__ == "__main__":
    main()