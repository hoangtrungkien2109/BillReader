from bill_classifier.bill_classifier_model import train_classifier_model, classify_image

if __name__ == '__main__':
    history = train_classifier_model("data/classification/", epochs=50)
    print(history)
