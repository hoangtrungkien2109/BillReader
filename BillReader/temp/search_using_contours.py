from utils import *
import pytesseract as pt
import glob

"""
Page segmentation modes:
  0    Orientation and script detection (OSD) only.
  1    Automatic page segmentation with OSD.
  2    Automatic page segmentation, but no OSD, or OCR.
  3    Fully automatic page segmentation, but no OSD. (Default)
  4    Assume a single column of text of variable sizes.
  5    Assume a single uniform block of vertically aligned text.
  6    Assume a single uniform block of text.
  7    Treat the image as a single text line.
  8    Treat the image as a single word.
  9    Treat the image as a single word in a circle.
 10    Treat the image as a single character.
 11    Sparse text. Find as much text as possible in no particular order.
 12    Sparse text with OSD.
 13    Raw line. Treat the image as a single text line,
 
OCR Engine modes:
0. Legacy engine only.
1. Neural nets LSTM engine only.
2. Legacy + LSTM engines.
3. Default, based on what is available.
 """

config = r"-l vie --oem 1"
image_paths = glob.glob("data/process/*")
for image_path in image_paths:
    image_filename = image_path.split("\\")[-1]
    print("Processing image {}".format(image_filename))
    image_name = image_filename.split(".")[0]
    img = cv2.imread(image_path)
    contours = find_contours(img)
    contours = sorted(contours, key=cv2.contourArea)
    res = []
    for contour in contours:
        rect = cv2.boundingRect(contour)
        x, y, w, h = rect
        if w * h > img.shape[0] * img.shape[1] // 3:
            break
        temp_img = img[y:y+h, x:x+w]
        config = r"-l vie --oem 1 --psm 7"
        temp_txt = no_accent_vietnamese(pt.image_to_string(temp_img, config=config))
        if "tong cong" in temp_txt.lower():
            res = [x, y, w, h]
            break
    if res:
        detect = draw_box(img, res[0], res[1], res[2], res[3])
        cv2.imwrite('temp/bill4_detect.png', detect)
