from ultralytics import YOLO
import cv2


def find_field_yolo(model_path, src_path):
    model = YOLO(model_path)
    results = model.predict(source=src_path, save=True, save_txt=True)
    return results


def train_yolo(yaml_path, runs_path, epochs, pretrained=None):
    if pretrained:
        model = YOLO(pretrained)
    model.train(data=yaml_path, epochs=epochs, resume=True if pretrained else False, project=runs_path)

if __name__ == "__main__":
    print(find_field_yolo("runs/detect/train9_50e_300train/weights/best.pt", "data/images"))