from torch import nn
from torch.utils.data import DataLoader
from BillReader.bill_classifier.load_data import MyDataLoader
from BillReader.bill_classifier.utils import *
from tqdm import tqdm
import json
import cv2
import glob


class ConvBlock(torch.nn.Module):
    def __init__(self, in_channels: int, out_channels: int, use_act: bool = False, use_bn: bool = False, **kwargs):
        super().__init__()
        self.conv = torch.nn.Conv2d(in_channels, out_channels, **kwargs, bias=True)
        self.bn = torch.nn.BatchNorm2d(out_channels, affine=True) if use_bn else nn.Identity()
        self.act = torch.nn.LeakyReLU(negative_slope=0.2, inplace=True) if use_act else nn.Identity()

    def forward(self, x):
        return self.act(self.bn(self.conv(x)))


class BillClassifier(nn.Module):
    def __init__(self, in_channels: int, features=None, num_classes: int = 2):
        super().__init__()
        if features is None:
            features = [64, 64, 128, 128]
        blocks = []
        for idx, feature in enumerate(features):
            blocks.append(
                ConvBlock(
                    in_channels,
                    feature,
                    kernel_size=3,
                    stride=1 + idx % 2,
                    padding=1,
                    use_act=True,
                    use_bn=True if idx < 3 else False
                )
            )
            in_channels = feature
        self.blocks = nn.Sequential(*blocks)
        self.classifier = nn.Sequential(
            nn.AdaptiveAvgPool2d((6, 6)),
            nn.Flatten(),
            nn.Linear(in_channels * 6 * 6, 256),
            nn.LeakyReLU(0.2, inplace=True),
            nn.Linear(in_features=256, out_features=num_classes),
            nn.Softmax(dim=1)
        )

    def forward(self, x):
        x = self.blocks(x)
        return self.classifier(x)


def train_classifier_model(root_dir, model_path, model: BillClassifier | None = None, epochs=10,
                           lr=1e-4, batch=4, load_model=False, device: str | None = None,
                           num_classes=2, hist_path=None):
    history = {"loss": [], "acc": []}
    if model is None:
        model = BillClassifier(in_channels=3, num_classes=num_classes)
    if not device:
        device = "cuda" if torch.cuda.is_available() else "cpu"
    dataloader = MyDataLoader(root_dir)
    initialize_weights(model)
    opt = torch.optim.Adam(model.parameters(), lr=lr, betas=(0.0, 0.9))
    loss_func = nn.CrossEntropyLoss()
    model.to(device)
    model.train()
    loader = DataLoader(
        dataloader,
        batch_size=batch,
        shuffle=True,
        pin_memory=True,
        num_workers=4
    )
    if load_model:
        load_checkpoint(
            model_path,
            model,
            opt,
            lr,
        )
    loop = tqdm(loader, leave=True)
    for epoch in tqdm(range(epochs)):
        running_loss = 0.0
        true_prediction = 0
        for idx, (image, label) in enumerate(loop):
            image = image.to(device)
            label = label.to(device)
            # one_hot_labels = F.one_hot(label, num_classes=num_classes)
            # Zero the parameter gradients
            opt.zero_grad()

            # Forward pass
            outputs = model(image)
            loss = loss_func(outputs, label)
            _, predicted = torch.max(outputs, dim=1)
            true_prediction += batch - torch.sum(predicted-label)
            # Backward pass and optimize
            loss.backward()
            opt.step()

            running_loss += loss.item()

        history["loss"].append(running_loss)
        history["acc"].append((true_prediction / (len(loop) * batch)).item())
        if (epoch+1) % 5 == 0:
            print(f"Epoch [{epoch+1}/{epochs}]")
            save_checkpoint(model, opt, filename=model_path)
    save_checkpoint(
        model,
        opt,
        filename=model_path
    )
    hist_json = json.dumps(history, indent=2)

    # Writing to sample.json
    if hist_path:
        with open(hist_path, "w") as outfile:
            outfile.write(hist_json)
    return history


def classify_image(img_path: str, model_path: str, num_classes: int,
                   device: str | None = None, lr=1e-4):
    base_model = BillClassifier(in_channels=3, num_classes=num_classes)
    opt = torch.optim.Adam(base_model.parameters(), lr=lr, betas=(0.0, 0.9))
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
    base_model.to(device)
    base_model.eval()
    load_checkpoint(
        model_path,
        base_model,
        opt,
        lr
    )
    if type(img_path) is str:
        image = cv2.imread(img_path)
    else:
        image = img_path
    image = transform(image=image)['image'].unsqueeze(0).to(device)
    with torch.no_grad():
        output = base_model(image)
        _, predicted = torch.max(output, dim=1)

    return predicted.item()


def initialize_weights(model, scale=0.1):
    for m in model.modules():
        if isinstance(m, nn.Conv2d):
            nn.init.kaiming_normal_(m.weight.data)
            m.weight.data *= scale

        elif isinstance(m, nn.Linear):
            nn.init.kaiming_normal_(m.weight.data)
            m.weight.data *= scale
