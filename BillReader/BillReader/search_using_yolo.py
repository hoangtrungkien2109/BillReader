from ultralytics import YOLO
import cv2

if __name__ == '__main__':
    model = YOLO("runs/detect/train9/weights/best.pt")
    results = model.predict(source="data/images", save=True, save_txt=True)