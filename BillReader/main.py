from utils import train_yolo, rename_file, augment_image, multiprocess_augment, find_corners
import glob
import cv2


if __name__ == '__main__':
    # multiprocess_augment(
    #     src_paths="data/yolo_detect_corner/raw",
    #     dst_paths=[
    #         "data/yolo_detect_corner/datatrain",
    #         "data/yolo_detect_corner/dataval",
    #         "data/yolo_detect_corner/datatest"
    #     ],
    #     multipliers=[3, 2, 1],
    # )
    # train_yolo(
    #     yaml_path="data/yolo_detect_corner/data.yaml",
    #     runs_path="data/yolo_detect_corner",
    #     epochs=100,
    # )
    find_corners("data/yolo_detect_corner/train_100e/weights/best.pt", "data/yolo_detect_corner/datatest")
    find_corners("data/yolo_detect_corner/train_100e/weights/best.pt", "data/bills1")
