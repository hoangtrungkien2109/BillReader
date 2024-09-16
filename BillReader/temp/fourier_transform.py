import cv2
import numpy as np
import matplotlib.pyplot as plt


def calculate_skew_from_magnitude_spectrum(magnitude_spectrum):
    # Get the dimensions of the image
    (h, w) = magnitude_spectrum.shape

    # Create a blank image to store the line values from the magnitude spectrum
    mask = np.zeros((h, w), dtype=np.uint8)

    # Define the center of the magnitude spectrum
    center = (w // 2, h // 2)

    # We are interested in the prominent vertical features, so we will look for peaks
    # along lines passing through the center.
    angles = np.arange(-90, 90, 0.5)
    max_votes = 0
    best_angle = 0

    # Search for prominent lines in the magnitude spectrum
    for angle in angles:
        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(magnitude_spectrum, rotation_matrix, (w, h))

        # Sum the pixel values along the vertical axis (row-wise)
        votes = np.sum(rotated[h // 2 - 10:h // 2 + 10, :])

        # Keep track of the angle with the highest vote (most prominent lines)
        if votes > max_votes:
            max_votes = votes
            best_angle = angle

    return best_angle


def fourier_skew_correction(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply FFT to the grayscale image
    f = np.fft.fft2(gray)
    fshift = np.fft.fftshift(f)

    # Compute the magnitude spectrum
    magnitude_spectrum = 20 * np.log(np.abs(fshift))

    # Normalize the magnitude spectrum for display and processing
    magnitude_spectrum = cv2.normalize(magnitude_spectrum, None, 0, 255, cv2.NORM_MINMAX)
    magnitude_spectrum = np.uint8(magnitude_spectrum)

    # Calculate the skew angle using the magnitude spectrum
    skew_angle = calculate_skew_from_magnitude_spectrum(magnitude_spectrum)

    return skew_angle


# Load the image and apply Fourier skew correction
image = cv2.imread('IMG_3086.jpg')
skew_angle = fourier_skew_correction(image)

# Apply rotation to correct skew
(h, w) = image.shape[:2]
center = (w // 2, h // 2)
rotation_matrix = cv2.getRotationMatrix2D(center, skew_angle, 1.0)
rotated_image = cv2.warpAffine(image, rotation_matrix, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

# Save or show the corrected image
cv2.imwrite('fourier_corrected_image.png', rotated_image)
