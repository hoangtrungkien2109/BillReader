import numpy as np


def find_value_coordinate(field_boxes, value_boxes):
    field_boxes_temp = field_boxes.copy()
    value_boxes_temp = value_boxes.copy()
    average_value_coordinate = [0, 0, 0, 0]
    for field_box, value_box in zip(field_boxes_temp, value_boxes_temp):
        field = [eval(i) for i in field_box.split(" ")[1:]]
        value = [eval(i) for i in value_box.split(" ")[1:]]
        average_value_coordinate[:2] = (np.array(average_value_coordinate[:2]) + np.array(value[:2]) - np.array(field[:2])).tolist()
        average_value_coordinate[2:] = (np.array(average_value_coordinate[2:]) + np.array(value[2:])).tolist()
    average_value_coordinate[:] = (np.array(average_value_coordinate[:]) / len(field_boxes)).tolist()
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
