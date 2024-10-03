import glob
import numpy as np
import cv2
import pytesseract as pt
import json
import os
from ultralytics import YOLO
from BillReader.field_detector.preprocess import preprocess


def split_field_value_from_annotation(annotation_file):
    with open(annotation_file, 'r') as f:
        lines = f.readlines()
    values = [line.replace('\n','') for line in lines[1:len(lines):2]]
    fields = [line.replace('\n','') for line in lines[0:len(lines):2]]
    with open(annotation_file, 'w') as f:
        f.writelines(lines[0:len(lines):2])
    return fields, values


def find_value_coordinate(field_boxes, value_boxes):
    field_boxes_temp = field_boxes.copy()
    value_boxes_temp = value_boxes.copy()
    average_value_coordinate = [0, 0, 0, 0]
    for field_box, value_box in zip(field_boxes_temp, value_boxes_temp):
        field = [eval(i) for i in field_box.split(" ")[1:]]
        value = [eval(i) for i in value_box.split(" ")[1:]]
        average_value_coordinate[:2] = np.array(average_value_coordinate[:2]) + np.array(value[:2]) - np.array(field[:2])
        average_value_coordinate[2:] = np.array(average_value_coordinate[2:]) + np.array(value[2:])
    average_value_coordinate[:] = (average_value_coordinate[:] / len(field_boxes)).tolist()
    return average_value_coordinate


def find_average_value_coordinate(value_boxes):
    value_boxes_temp = value_boxes.copy()
    average_value_coordinate = np.array([0., 0., 0., 0.])
    for value_box in value_boxes_temp:
        value = [eval(i) for i in value_box.split("_")]
        average_value_coordinate = average_value_coordinate + np.array(value)
    for idx in range(len(average_value_coordinate)):
        average_value_coordinate[idx] /= 5
    print(value_boxes_temp[0], average_value_coordinate)
    return average_value_coordinate.tolist()


def detect_value_box(field_box, value_coordinate, multiplier: float = 1.4):
    value = value_coordinate.copy()
    # field_box = [eval(i) for i in field_box.split(" ")[1:]]
    value[0] += field_box[0]
    value[1] += field_box[1]
    value[2] = value[2] * multiplier
    value[3] = value[3] * multiplier
    return value


def denormalize(image, field_box, value_box):
    value = value_box.copy()
    field = field_box.copy()
    # field = [eval(i) for i in field.split(" ")[1:]]
    for i in range(4):
        field[i] = int(field[i] * image.shape[1 - (i % 2)])
        value[i] = int(value[i] * image.shape[1 - (i % 2)])
    return field, value


def get_value_coordinates_from_annotation_file(src_path: str = "data/yolo_detect_multifield_box/",
                                               num_classes: int = 2):
    image_paths = glob.glob(src_path + "/*.jpg")
    field_paths = glob.glob(src_path + "/*.txt")
    value_paths = glob.glob(src_path + "/*.txt")
    field_coordinates = np.array([[] for _ in range(num_classes)])
    value_coordinates = np.array([[] for _ in range(num_classes)])
    for image_path, field_path, value_path in zip(image_paths, field_paths, value_paths):
        field_coordinate = [[] for _ in range(num_classes)]
        value_coordinate = [[] for _ in range(num_classes)]
        with open(field_path, "r") as field_file:
            for i in range(num_classes):
                field_coordinate[i].append(field_file.readline().split("\n")[0])
        with open(value_path, "r") as value_file:
            for i in range(num_classes):
                value_coordinate[i].append(value_file.readline().split("\n")[0])
        field_coordinates = np.hstack((field_coordinates, np.array(field_coordinate)))
        value_coordinates = np.hstack((value_coordinates, np.array(value_coordinate)))

    average_values_coordinate = []
    for i in range(num_classes):
        average_values_coordinate.append(find_value_coordinate(field_coordinates[i].tolist(),
                                                               value_coordinates[i].tolist()))
    return average_values_coordinate


def retrieve_values_from_coordinates(src_path, dst_path, field_coordinates, average_values_coordinate, classes):
    config = r"-l vie --oem 1"
    image_paths = glob.glob(src_path + "/*.jpg")
    print(field_coordinates)
    for idx, image_path in enumerate(image_paths):
        values = {}
        image_name = image_path.split("\\")[-1]
        image = cv2.imread(image_path)
        result_path = dst_path + "/" + image_name.split(".")[0] + ".txt"
        with open(result_path, "w") as f:
            for i in range(len(classes)):
                field_box = field_coordinates[i][idx]
                value_box = detect_value_box(field_box, average_values_coordinate[i], multiplier=1.2)
                field_box, value_box = denormalize(image, field_box, value_box)
                x_val, y_val, w_val, h_val = value_box

                # Need to process the result
                result = pt.image_to_string(
                    image[y_val-h_val//2:y_val+h_val//2, x_val-w_val//2:x_val+w_val//2],
                    config=config
                )
                cv2.rectangle(image, (x_val-w_val//2, y_val-h_val//2), (x_val+w_val//2, y_val+h_val//2),
                              (255, 0, 0), 3)
                cv2.imwrite("result/" + image_name.split(".")[0] + ".png", image)
                print(result)
                values[classes[i]] = result
            # json.dump(values)
            f.write(json.dumps(values))
        #     image = cv2.rectangle(image, pt1=(int(field_box[0]-field_box[2]//2), int(field_box[1]-field_box[3]//2)),
        #                           pt2=(int(field_box[0]+field_box[2]//2), int(field_box[1]+field_box[3]//2)),
        #                           color=(255,0,0), thickness=3)
        #
        #     image = cv2.rectangle(image, pt1=(int(value_box[0]-value_box[2]//2), int(value_box[1]-value_box[3]//2)),
        #                           pt2=(int(value_box[0]+value_box[2]//2), int(value_box[1]+value_box[3]//2)),
        #                           color=(0,255,0), thickness=3)
        #
        #     image = cv2.line(image, pt1=(int(field_box[0]), int(field_box[1])),
        #                      pt2=(int(value_box[0]), int(value_box[1])),
        #                      color=(0,0,255), thickness=2)
        # cv2.imwrite("data/yolo_detect_multifield_box/detected_values/" + image_name, image)


def extract_bill_from_image(img_dir: str, dst_dir: str, extension: str = ".jpg") -> None:
    image_paths = glob.glob(img_dir + '/*' + extension)
    for image_path in image_paths:
        image_filename = image_path.split('\\')[-1]
        print("Processing image {}".format(image_filename))
        image = cv2.imread(image_path)
        image = preprocess(image)
        cv2.imwrite(dst_dir + "/" + image_filename, image)


def find_field_yolo(model_path, src_path, save=False):
    model = YOLO(model_path)
    results = model.predict(source=src_path, save=save, save_txt=save)
    return results


def train_yolo(yaml_path, runs_path, epochs, pretrained=None):
    if pretrained:
        model = YOLO(pretrained)
    else:
        model = YOLO("yolov8n.pt")
    model.train(data=yaml_path, epochs=epochs, resume=True if pretrained else False, project=runs_path)
