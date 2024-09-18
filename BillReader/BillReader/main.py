import glob
import numpy as np
from detect_value_from_field import find_value_coordinate, detect_value_box, denormalize
import cv2

num_classes = 2
path = "data/yolo_detect_multifield_box/"
image_paths = glob.glob(path + "raw2/*.jpg")
field_paths = glob.glob(path + "raw2/*.txt")
value_paths = glob.glob(path + "val_annotation_raw2/*.txt")
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
print(average_values_coordinate)

for idx, (image_path, field_path, value_path) in enumerate(zip(image_paths, field_paths, value_paths)):
    image_name = image_path.split("\\")[-1]
    image = cv2.imread(image_path)
    for i in range(num_classes):
        field_box = field_coordinates[i][idx]
        value_box = detect_value_box(field_box, average_values_coordinate[i])
        field_box, value_box = denormalize(image, field_box, value_box)
        print(value_box[0]-value_box[2]//2)
        image = cv2.rectangle(image, pt1=(int(field_box[0]-field_box[2]//2), int(field_box[1]-field_box[3]//2)),
                              pt2=(int(field_box[0]+field_box[2]//2), int(field_box[1]+field_box[3]//2)),
                              color=(255,0,0), thickness=3)

        image = cv2.rectangle(image, pt1=(int(value_box[0]-value_box[2]//2), int(value_box[1]-value_box[3]//2)),
                              pt2=(int(value_box[0]+value_box[2]//2), int(value_box[1]+value_box[3]//2)),
                              color=(0,255,0), thickness=3)
    cv2.imwrite("data/yolo_detect_multifield_box/detected_values/" + image_name, image)