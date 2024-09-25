import numpy as np
import cv2


def threshold_image(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # cv2.imwrite('temp/imgray.png', gray)
    blurred = cv2.GaussianBlur(gray, (9, 9), 0)
    # cv2.imwrite('temp/imblur.png', blurred)
    thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    # cv2.imwrite('temp/imthresh.png', thresh)
    return thresh


def find_largest_contour(image):
    contours, _ = cv2.findContours(image.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    return max(contours, key=cv2.contourArea)


def get_min_area_rect(contour):
    return cv2.minAreaRect(contour)


def rotate_image(image, angle):
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(image, rotation_matrix, (w, h), flags=cv2.INTER_LINEAR)


def extract_rotated_bill(image):
    original = image.copy()

    # Preprocess the image
    thresh = threshold_image(image)

    # Find the largest contour (assumed to be the bill)
    contour = find_largest_contour(thresh)
    if contour is None:
        print("No contour found in the image")
        return None

    # Get the minimum area rectangle
    rect = get_min_area_rect(contour)
    box = cv2.boxPoints(rect)
    box = np.int64(box)

    # Get the angle of rotation
    angle = rect[2]
    if angle < -45:
        angle += 90
    if angle > 45:
        angle -= 90

    # Rotate the image
    rotated = rotate_image(original, angle)
    print(angle)
    # Crop the rotated image
    (x, y, w, h) = cv2.boundingRect(box)
    cropped = rotated[y:y + h, x:x + w]

    return cropped


def remove_borders(image):
    new_img = threshold_image(image)
    contours, hierarchy = cv2.findContours(new_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    max_cnt = max(contours, key=lambda c: cv2.contourArea(c))
    x, y, w, h = cv2.boundingRect(max_cnt)
    crop = image[y:y+h, x:x+w]
    return crop


def remove_noise(image):
    kernel = np.ones((1, 1), np.uint8)
    image = cv2.dilate(image, kernel, iterations=1)
    kernel = np.ones((1, 1), np.uint8)
    image = cv2.erode(image, kernel, iterations=1)
    image = cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)
    image = cv2.medianBlur(image, 3)
    return image


def preprocess(image):
    image = extract_rotated_bill(image)
    image = remove_borders(image)
    image = remove_noise(image)
    return image


def find_contours(img):
    image = img.copy()
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (9, 9), 0)
    thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (30, 5))
    dilate = cv2.dilate(thresh, kernel, iterations=1)
    contours, _ = cv2.findContours(dilate.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return contours
