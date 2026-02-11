import cv2
import os

def run_edge_blend(image_path: str) -> None:
    # Load image
    color = cv2.imread(image_path)
    if color is None:
        raise FileNotFoundError(f"Could not load image: {image_path}")

    # output filename
    base, _ext = os.path.splitext(image_path)
    outfile = base + ".edges.jpg"

    # convert to grayscale
    gray = cv2.cvtColor(color, cv2.COLOR_BGR2GRAY)

    # create the output window
    cv2.namedWindow("image")

    # create trackbars
    cv2.createTrackbar("blend", "image", 0, 100, lambda x: None)
    cv2.createTrackbar("thresh", "image", 0, 255, lambda x: None)
    cv2.createTrackbar("blur", "image", 0, 31, lambda x: None)

    blended = color  # so it exists even before loop runs

    while True:
        blend = cv2.getTrackbarPos("blend", "image")
        thresh = cv2.getTrackbarPos("thresh", "image")
        k = cv2.getTrackbarPos("blur", "image")

        k = max(1, k)
        if k % 2 == 0:
            k += 1
        k = min(31, k)
        cv2.setTrackbarPos("blur", "image", k)

        alpha = blend / 100.0
        beta = 1.0 - alpha

        blur_img = cv2.GaussianBlur(gray, (k, k), 0)

        dx = cv2.Sobel(blur_img, cv2.CV_64F, 1, 0, ksize=3)
        dy = cv2.Sobel(blur_img, cv2.CV_64F, 0, 1, ksize=3)
        mag = cv2.magnitude(dx, dy)
        grad = cv2.convertScaleAbs(mag)

        _, edges = cv2.threshold(grad, thresh, 255, cv2.THRESH_BINARY)

        edges_color = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)

        blended = cv2.addWeighted(color, beta, edges_color, alpha, 0)

        cv2.imshow("image", blended)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break

    cv2.destroyAllWindows()
    cv2.imwrite(outfile, blended)
    print(f"Saved: {outfile}")


if __name__ == "__main__":
    # change this to any image you want
    # run_edge_blend("edges/GoldenGateBridge.jpg") 
    # run_edge_blend("edges/BushnellUniversity.jpg")
    # run_edge_blend("edges/MonaLisa.jpg")
    # run_edge_blend("edges/QRCode.jpg")
    run_edge_blend("edges/USCapitol.jpg")
