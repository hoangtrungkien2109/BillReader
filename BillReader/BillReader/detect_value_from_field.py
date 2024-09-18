import numpy as np


def find_value_coordinate(field_boxes, value_boxes):
    average_value_coordinate = [0, 0, 0, 0]
    for field_box, value_box in zip(field_boxes, value_boxes):
        field = [eval(i) for i in field_box.split(" ")[1:]]
        value = [eval(i) for i in value_box.split(" ")[1:]]
        average_value_coordinate[:2] = (np.array(average_value_coordinate[:2]) + np.array(value[:2]) - np.array(field[:2])).tolist()
        average_value_coordinate[2:] = (np.array(average_value_coordinate[:2]) + np.array(value[2:])).tolist()
    average_value_coordinate[:] = (np.array(average_value_coordinate[:]) / len(field_boxes)).tolist()
    return average_value_coordinate


def detect_value_box(field_box, value_coordinate, multiplier: float = 1.6):
    field_box = [eval(i) for i in field_box.split(" ")[1:]]
    value_coordinate[0] += field_box[0] - value_coordinate[2] * 1.1
    value_coordinate[1] += field_box[1]
    value_coordinate[2] = value_coordinate[2] * multiplier * 1.2
    value_coordinate[3] = value_coordinate[3] * multiplier
    return value_coordinate


def denormalize(image, field_box, value_box):
    field_box = [eval(i) for i in field_box.split(" ")[1:]]
    for i in range(4):
        field_box[i] = int(field_box[i] * image.shape[1 - (i % 2)])
        value_box[i] = int(value_box[i] * image.shape[1 - (i % 2)])
    return field_box, value_box
