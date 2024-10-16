# from BillReader.field_detector.preprocess import *
import re
import cv2
import glob
import torchvision.transforms as transforms
from PIL import Image
import numpy
import random
import os
import shutil
from multiprocessing import Process


def augment_image(src: str, dst: str, multiplier: int, start: int = 0, end: int | None = None,
                  classification: bool = False):
    """
    :param src: Source image path, including annotation txt file
    :param dst: Destination image path
    :param multiplier: Amount that will be multiplied with images in src_path
    :param start: Start index of image in src_path
    :param end: End index of image in src_path
    :param classification: To determine whether to classify or to detect
    """
    image_paths = glob.glob(src + "/*.jpg")
    if not os.path.exists(dst):
        os.makedirs(dst)
    if end is None:
        end = len(image_paths)
    for image_path in image_paths[start:end]:
        image_filename = image_path.split('\\')[-1]
        image_name = image_filename.split('.')[0]
        image = Image.open(image_path)
        for i in range(multiplier):

            # Create augmented images
            random_num = []
            for temp in range(4):
                random_num.append(random.uniform(0, 0.5))
            transform = transforms.Compose([
                transforms.ColorJitter(brightness=random_num[0], contrast=random_num[1], saturation=random_num[2], hue=random_num[3]),
                transforms.Resize((1024, 1024))
            ])
            random_image = transform(image).convert('RGB')
            random_image = numpy.array(random_image)
            random_image = random_image[:, :, ::-1].copy()
            cv2.imwrite(dst + "/" + image_name + str(i) + ".jpg", random_image)
            if not classification:
                # Save corresponding annotations
                src_folder = src
                dst_folder = dst
                filename = image_name + str(i) + ".txt"

                # Set the filename to copy and the new name
                old_filename = image_name + '.txt'

                # Construct the full paths
                src_path = os.path.join(src_folder, old_filename)
                dst_path = os.path.join(dst_folder, filename)

                # Copy the file and rename it
                shutil.copy2(src_path, dst_path)


def multiprocess_augment(src_paths, dst_paths=None, multipliers=None, max_amounts=None, classification: bool = False,
                         starts=None, ends=None):
    processes = []
    if classification:
        for idx, src_path in enumerate(src_paths):
            p = Process(
                target=augment_image,
                args=(
                    src_path,
                    dst_paths[idx],
                    multipliers[idx] if multipliers else (max_amounts[idx] // len(glob.glob(src_path + "/*"))),
                    0, None, classification
            ))
            processes.append(p)
    else:
        for idx, dst_path in enumerate(dst_paths):
            p = Process(
                target=augment_image,
                args=(
                    src_paths,
                    dst_path,
                    multipliers[idx] if multipliers else (max_amounts[idx] // len(glob.glob(src_paths + "/*"))),
                    starts[idx] if starts else 0,
                    ends[idx] if ends else None
            ))
            processes.append(p)
    for p in processes:
        p.start()
    for p in processes:
        p.join()


def detach_annotations(src_path, dst_path_1, dst_path_2, num_detach: int = 2):
    annotation_paths = glob.glob(src_path + '/*.txt')
    for annotation_path in annotation_paths:
        filename = annotation_path.split('\\')[-1]
        with open(annotation_path, 'r') as f:
            lines = f.readlines()
        with open(dst_path_1 + '/' + filename, 'w') as f2:
            f2.write("".join(lines[:num_detach]))
        with open(dst_path_2 + '/' + filename, 'w') as f2:
            f2.write("".join(lines[num_detach:]))


def no_accent_vietnamese(s):
    s = re.sub(r'[àáạảãâầấậẩẫăằắặẳẵ]', 'a', s)
    s = re.sub(r'[èéẹẻẽêềếệểễ]', 'e', s)
    s = re.sub(r'[òóọỏõôồốộổỗơờớợởỡ]', 'o', s)
    s = re.sub(r'[ìíịỉĩ]', 'i', s)
    s = re.sub(r'[ùúụủũưừứựửữ]', 'u', s)
    s = re.sub(r'[ỳýỵỷỹ]', 'y', s)
    s = re.sub(r'[đ]', 'd', s)
    return s


def rename_file(src_path):
    img_paths = glob.glob(src_path + "/*.jpg")
    ann_paths = glob.glob(src_path + "/*.txt")
    cnt = 1
    for img_path, ann_path in zip(img_paths, ann_paths):
        new_name = "bill" + str(cnt)
        os.rename(img_path, img_path.split("\\")[0] + "/" + new_name + ".jpg")
        os.rename(ann_path, ann_path.split("\\")[0] + "/" + new_name + ".txt")
        cnt += 1
