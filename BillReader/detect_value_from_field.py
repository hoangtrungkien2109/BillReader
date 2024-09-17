import glob
import numpy as np
import cv2
import pytesseract as pt
import json


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


def detect_value_box(field_box, value_coordinate, multiplier: float = 1.4):
    value = value_coordinate.copy()
    field_box = [eval(i) for i in field_box.split(" ")[1:]]
    value[0] += field_box[0]
    value[1] += field_box[1]
    value[2] = value[2] * multiplier
    value[3] = value[3] * multiplier
    return value


def denormalize(image, field_box, value_box):
    value = value_box.copy()
    field = field_box.copy()
    field = [eval(i) for i in field.split(" ")[1:]]
    for i in range(4):
        field[i] = int(field[i] * image.shape[1 - (i % 2)])
        value[i] = int(value[i] * image.shape[1 - (i % 2)])
    return field, value


def get_value_coordinates_from_annotation_file(src_path: str = "data/yolo_detect_multifield_box/", num_classes: int = 2):
    image_paths = glob.glob(src_path + "raw2/*.jpg")
    field_paths = glob.glob(src_path + "raw2/*.txt")
    value_paths = glob.glob(src_path + "val_annotation_raw2/*.txt")
    field_coordinates = np.array([[], []])
    value_coordinates = np.array([[], []])
    for image_path, field_path, value_path in zip(image_paths, field_paths, value_paths):
        field_coordinate = [[], []]
        value_coordinate = [[], []]
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
        average_values_coordinate.append(find_value_coordinate(field_coordinates[i].tolist(), value_coordinates[i].tolist()))
    return average_values_coordinate


def retrieve_values_from_coordinates(src_path, dst_path, field_coordinates, average_values_coordinate, classes):
    config = r"-l vie --oem 1"
    image_paths = glob.glob(src_path + "raw2/*.jpg")
    for idx, image_path in enumerate(image_paths):
        values = {}
        image_name = image_path.split("\\")[-1]
        image = cv2.imread(image_path)
        with open(dst_path + "/" + image_name.split(".")[0] + ".txt", "w") as f:
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
                values[classes[i]] = result
                json.dump(values)
                f.write(classes[i] + ": " + result)
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