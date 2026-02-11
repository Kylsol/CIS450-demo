# CIS450-demo
## Introduction
This repo illustrates best practice README file generation
## Projects
Open-CV image processing demos
## Resources
<img src="./images/OpenCV_logo_black_.png" alt="OpenCV logo" width="100"/>

[Open-CV](https://opencv.org)

## Edge Detection

Edge detection identifies areas in an image where brightness changes rapidly.  
The image is converted to grayscale to simplify processing.  
Gaussian blur is applied to reduce noise.  
Sobel filters compute horizontal and vertical intensity changes.  
Thresholding removes weak edges and keeps important outlines.

## Image Blending

Image blending combines two images into one output.  
The edge image is overlaid on the original color image.  
Both images must have the same size and color channels.  
OpenCV’s `addWeighted()` function controls how much of each image is shown.
