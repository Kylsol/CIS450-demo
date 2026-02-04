import cv2 as cv
import sys
import os

print("Currenct working directory: ", os.get)

img = cv.imread("photos/panarama1/IG_0638.png")
print(img.shape)

if img is None:
    sys.exit("Could not read the image.")

cv.namedWindow("Display window", cv.WINDOW_NORMAL)
cv.resizeWindow("Display window", 800, 600)

cv.imshow("Display window", img)
k = cv.waitkey(0)

resized_image = cv.resize(img, (640, 400), dst=None, fx=None, fy=None, interpolation=cv.INTER_LINEAR)
filename = "photos/panorama1/IMG-640x480.png"
cv.imwrite(filename, resized_image)
print(f"image saved tp {filename}")
