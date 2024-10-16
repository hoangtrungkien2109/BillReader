from BillReader.corner_detector.corner_detector import detect_corner
from BillReader.field_detector.value_extractor import (retrieve_values_from_coordinates, find_field_yolo,
                                                       find_average_value_coordinate, train_yolo)
from BillReader.bill_classifier.bill_classifier_model import train_classifier_model, classify_image
from BillReader.utils import multiprocess_augment
from Flask.src.database import users, bills, accounts
from loguru import logger
import os
import yaml
import shutil
import glob
import json


UPLOAD_FOLDER = 'image'
TRAIN_FOLDER = 'training_model_temp_folder'
MODEL_FOLDER = 'models'


class ValueDetector:
    def __init__(self, username, class_list, bill_type):
        self.class_list = class_list
        self.bill_type = bill_type
        self.username = username

    def train_model(self):
        origin_folder = os.path.join(TRAIN_FOLDER, 'origin')
        train_folder = os.path.join(TRAIN_FOLDER, 'train')
        val_folder = os.path.join(TRAIN_FOLDER, 'val')
        model_folder = os.path.join(MODEL_FOLDER, self.username)
        new_model_folder = os.path.join(UPLOAD_FOLDER, self.username, self.bill_type)
        if not os.path.exists(origin_folder):
            os.makedirs(origin_folder)
        if not os.path.exists(train_folder):
            os.makedirs(train_folder)
        if not os.path.exists(val_folder):
            os.makedirs(val_folder)
        if not os.path.exists(model_folder):
            os.makedirs(model_folder)
        if not os.path.exists(new_model_folder):
            os.makedirs(new_model_folder)

        # Edit yaml file for training YOLO
        yaml_path = os.path.join(TRAIN_FOLDER, 'data.yaml')
        with open(yaml_path) as f:
            content = yaml.safe_load(f)
        content['path'] = "Flask/" + TRAIN_FOLDER
        content['train'] = 'train'
        content['val'] = 'val'
        content['nc'] = len(self.class_list)
        content['names'] = {}
        for idx, class_name in enumerate(self.class_list):
            content['names'][idx] = class_name
        with open(yaml_path, "w") as f:
            yaml.dump(content, f)

        # Copy original image to temporary folder
        image_list = users.find({'user': self.username, 'type': 'label'})
        ann_list = users.find({'user': self.username, 'type': 'coordinate'})
        for image, ann in zip(image_list, ann_list):
            shutil.copy(image['path'], origin_folder)
            shutil.copy(ann['path'], origin_folder)
        multiprocess_augment(
            src_paths=origin_folder,
            dst_paths=[train_folder, val_folder],
            multipliers=[70, 40],
            starts=[0, 3],
            ends=[4, 5]
        )

        #train YOLO model for field detecting
        try:
            train_yolo(yaml_path=yaml_path, runs_path=model_folder, epochs=20)
            weight_path = model_folder + "/train/weights/best.pt"
            shutil.copy(weight_path, new_model_folder)
        finally:
            # shutil.rmtree(model_folder)
            shutil.rmtree(train_folder)
            shutil.rmtree(val_folder)
            shutil.rmtree(origin_folder)
            for f in glob.glob(TRAIN_FOLDER + "/*.cache"):
                os.remove(f)

    def find_average_value(self):
        images_list = users.find({'user': self.username, 'type': 'label', 'bill_type': self.bill_type})

        class_list = [str(i) for i in range(len(images_list.clone()[0]['values']))]
        logger.info(class_list)
        # Create temporary folders
        model_folder = os.path.join(UPLOAD_FOLDER, self.username, self.bill_type)
        model_path = os.path.join(model_folder, "best.pt")
        json_path = os.path.join(model_folder, "average_values_coords.json")
        if not os.path.exists(model_path):
            if not os.path.exists(model_folder):
                os.makedirs(model_folder)

            self.train_model()
        if not os.path.exists(json_path):
            average_values_coords = []
            for _class in class_list:
                values_coords = []
                for image in images_list.clone():
                    values_coords.append(image['values'][_class])
                average_values_coords.append(find_average_value_coordinate(values_coords))
            temp_json = {"average_coords": average_values_coords}
            with open(os.path.join(model_folder, 'average_values_coords.json'), 'w') as f:
                json.dump(temp_json, f)
        with open(os.path.join(model_folder, 'average_values_coords.json'), 'r') as f:
            average_values_coords = json.load(f)['average_coords']
        return average_values_coords

    def detect(self, average_values_coords=None):
        if average_values_coords is None:
            average_values_coords = self.find_average_value()
        field_coords = [[] for _ in range(len(self.class_list))]
        src_path = os.path.join(UPLOAD_FOLDER, self.username, self.bill_type)
        result_path = os.path.join(src_path, "result")
        if not os.path.exists(result_path):
            os.makedirs(result_path)
        images = users.find({'user': self.username, 'bill_type': self.bill_type, 'type': 'train'})
        for image in images:
            field_coords = [[] for _ in range(len(self.class_list))]
            image_path = image['path']
            try:
                result = find_field_yolo(src_path + "/best.pt", image_path)
                for _result in result:
                    for box in _result.boxes:
                        x, y, w, h = box.xywh.tolist()[0]
                        x = x / box.orig_shape[1]
                        y = y / box.orig_shape[0]
                        w = w / box.orig_shape[1]
                        h = h / box.orig_shape[0]
                        field_coords[int(box.cls.item())].append([x, y, w, h])
                image_name = image_path.split("\\")[-1]
                result_path_temp = result_path + "/" + image_name.split(".")[0] + ".txt"
                with open(result_path_temp, "w") as f:
                    retrieve_values_from_coordinates(image_path, f, field_coords,
                                                     average_values_coords, classes=self.class_list)
            except FileNotFoundError:
                print("File not found")


class BillClassifier:
    def __init__(self, username, bill_list):
        self.bill_list = bill_list
        self.username = username
        self.model_folder = os.path.join(UPLOAD_FOLDER, self.username, "classifier.pth")

    def train_model(self):
        data_root = os.path.join(TRAIN_FOLDER, 'data')
        origin_root = os.path.join(TRAIN_FOLDER, 'origin')
        if not os.path.exists(data_root):
            os.makedirs(data_root)
        if not os.path.exists(origin_root):
            os.makedirs(origin_root)
        data_folders = []
        origin_folders = []
        for bill in self.bill_list:
            data_folder = os.path.join(data_root, bill)
            origin_folder = os.path.join(origin_root, bill)
            if not os.path.exists(data_folder):
                os.makedirs(data_folder)
            if not os.path.exists(origin_folder):
                os.makedirs(origin_folder)
            data_folders.append(data_folder)
            origin_folders.append(origin_folder)
            image_list = users.find({'user': self.username, 'type': 'label', 'bill_type': bill})
            for image in image_list:
                shutil.copy(image['path'], origin_folder)

        try:
            multiprocess_augment(src_paths=origin_folders, dst_paths=data_folders,
                                 multipliers=[40 for _ in range(len(data_folders))], classification=True)
            train_classifier_model(root_dir=data_root, model_path=self.model_folder,
                                   epochs=5, num_classes=len(self.bill_list),
                                   hist_path=os.path.join(UPLOAD_FOLDER, self.username, 'hist.json'))
        finally:
            shutil.rmtree(data_root)
            shutil.rmtree(origin_root)

    def classify(self, img_path):
        return classify_image(img_path=img_path, model_path=self.model_folder, num_classes=len(self.bill_list))
