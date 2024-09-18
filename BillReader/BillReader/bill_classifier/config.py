import torch
import albumentations as A
from albumentations.pytorch import ToTensorV2

LOAD_MODEL = True  # Chỉnh về False ở lần train đầu tiên
SAVE_MODEL = True
CHECKPOINT_PATH = "weight/classifier.pth"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
LEARNING_RATE = 1e-4
NUM_EPOCHS = 10
BATCH_SIZE = 2
NUM_WORKERS = 4
IMG_CHANNELS = 3

transform = A.Compose(
    [
        A.Normalize(mean=[0, 0, 0], std=[1, 1, 1]),
        ToTensorV2(),
    ]
)
