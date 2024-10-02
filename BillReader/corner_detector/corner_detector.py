import cv2
import numpy as np
from ultralytics import YOLO


def calculate_iou(box1, box2):
    """
    Calculate the Intersection over Union (IoU) of two bounding boxes.

    Parameters:
    box1: list or tuple of (x1, y1, x2, y2) where:
        (x1, y1) is the top-left corner,
        (x2, y2) is the bottom-right corner
    box2: list or tuple of (x1, y1, x2, y2)

    Returns:
    IoU: float
    """

    # Unpack the coordinates of each box
    x1_box1, y1_box1, x2_box1, y2_box1 = box1
    x1_box2, y1_box2, x2_box2, y2_box2 = box2

    # Calculate the coordinates of the intersection rectangle
    x1_inter = max(x1_box1, x1_box2)
    y1_inter = max(y1_box1, y1_box2)
    x2_inter = min(x2_box1, x2_box2)
    y2_inter = min(y2_box1, y2_box2)

    # Compute the area of intersection
    inter_width = max(0, x2_inter - x1_inter)
    inter_height = max(0, y2_inter - y1_inter)
    area_intersection = inter_width * inter_height

    # Compute the area of both the boxes
    area_box1 = (x2_box1 - x1_box1) * (y2_box1 - y1_box1)
    area_box2 = (x2_box2 - x1_box2) * (y2_box2 - y1_box2)

    # Compute the area of union
    area_union = area_box1 + area_box2 - area_intersection

    # Compute IoU
    if area_union == 0:
        return 0  # Avoid division by zero
    iou = area_intersection / area_union

    return iou


def detect_corner(model_path, img_path, dst_path=None, is_image_path=False):
    model = YOLO(model_path)
    results = model.predict(source=img_path, save=False, save_txt=False)
    if is_image_path:
        img = cv2.imread(img_path)
    else:
        img = img_path
    inp = [[], [], [], []]
    # results = find_corners("data/yolo_detect_corner/train_100e/weights/best.pt", "img.jpg")
    boxes = results[0].boxes
    print(len(boxes.xywh))
    iou_boxes = []
    for box in boxes.xyxy:
        not_skip = True
        x, y, x2, y2 = box[0].item(), box[1].item(), box[2].item(), box[3].item()
        for temp_box in iou_boxes:
            if calculate_iou(temp_box, [x, y, x2, y2]) > 0:
                not_skip = False
                continue
        if not_skip:
            iou_boxes.append([x, y, x2, y2])
    if len(iou_boxes) == 4:
        for box in iou_boxes:
            x, y = (box[0] + box[2]) // 2, (box[1] + box[3]) // 2
            if x > img.shape[1] // 2 and y > img.shape[0] // 2:
                inp[0] = [x, y]
            elif x < img.shape[1] // 2 and y > img.shape[0] // 2:
                inp[1] = [x, y]
            elif x < img.shape[1] // 2 and y < img.shape[0] // 2:
                inp[2] = [x, y]
            else:
                inp[3] = [x, y]
        [height, width] = (np.max(np.array(inp), axis=0) - np.min(np.array(inp), axis=0)).tolist()
        out = np.float32([[height, width], [0, width], [0, 0], [height, 0]])
        inp = np.float32(inp)
        transform_matrix = cv2.getPerspectiveTransform(inp, out)
        warp_img = cv2.warpPerspective(img, transform_matrix, (int(height), int(width)))
        if dst_path is not None:
            print(dst_path)
            cv2.imwrite(dst_path, warp_img)
        return warp_img
    else:
        print("no box found")
        return None
