import cv2
import numpy as np
from ultralytics import YOLO


def detect_corner(model_path, img_path, dst_path=None):
    model = YOLO(model_path)
    results = model.predict(source=img_path, save=False, save_txt=False)
    img = cv2.imread(img_path)
    out = np.float32([[img.shape[1], img.shape[0]], [0, img.shape[0]], [0, 0], [img.shape[1], 0]])
    inp = []
    # results = find_corners("data/yolo_detect_corner/train_100e/weights/best.pt", "img.jpg")
    boxes = results[0].boxes
    for box in boxes.xywh:
        inp.append([box[0].item(), box[1].item()])
    inp = np.float32(inp)
    transform_matrix = cv2.getPerspectiveTransform(inp, out)
    warp_img = cv2.warpPerspective(img, transform_matrix, (img.shape[1], img.shape[0]))
    # cv2.imwrite("warpimg.jpg", warp_img)
    return warp_img