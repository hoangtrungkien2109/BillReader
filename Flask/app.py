from flask import Flask, redirect, url_for, render_template, request, session, flash, send_file, jsonify
import os, cv2
from datetime import timedelta
from pymongo import MongoClient
from werkzeug.utils import secure_filename
import numpy as np
import yaml
import shutil
from BillReader.utils import multiprocess_augment
from BillReader.bill_classifier.bill_classifier_model import train_classifier_model, classify_image
from BillReader.corner_detector.corner_detector import detect_corner
from BillReader.field_detector.value_extractor import (retrieve_values_from_coordinates, find_value_coordinate,
                                                       detect_value_box, get_value_coordinates_from_annotation_file,
                                                       find_field_yolo, train_yolo, extract_bill_from_image,
                                                       split_field_value_from_annotation, find_average_value_coordinate)

app = Flask(__name__)
app._static_folder = ''
app.config['UPLOAD_FOLDER'] = 'Image'
app.config['TRAIN_FOLDER'] = 'training_model_temp_folder'
app.config['MODEL_FOLDER'] = 'models'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


app.secret_key = "123"
app.permanent_session_lifetime = timedelta(minutes=100)

# Thiết lập kết nối MongoDB
uri = "mongodb+srv://hoangtrungkien4:R22QsguGNpBfTHlw@billreader.kc3jt.mongodb.net/?retryWrites=true&w=majority&appName=BillReader"
client = MongoClient(uri)

db = client['my_database']
accounts = db['account']
users = db['user']


@app.route("/")
def home():
    if "username" in session:
        username = session["username"]
    else:
        username = 'Guest'
    return render_template("index.html", username=username)


@app.route('/Login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form["username"]
        password = request.form["password"]
        session["username"] = username

        # Tìm người dùng trong MongoDB
        user = accounts.find_one({'username': username, 'password': password})
        if user:
            flash('Đăng nhập thành công!')
            return redirect('/')
        else:
            return render_template('Login.html',message='Tên đăng nhập hoặc mật khẩu không đúng')
    return render_template('Login.html')


@app.route('/Signup', methods=['GET', 'POST'])
def Signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Thêm người dùng mới vào MongoDB
        if accounts.find_one({'username': username}):
            return render_template('Signup.html', message='Tài khoản đã tồn tại')
        else:
            new_user = {'username': username, 'password': password}
            accounts.insert_one(new_user)
            return render_template('Signup.html', message='Đăng ký thành công!')
    return render_template('Signup.html')


@app.route("/Logout")
def logout():
    session.pop("username", None)
    return render_template('Login.html', message='Đăng xuất thành công!')


@app.route('/Upload/<username>', methods=['GET', 'POST'])
def upload_file(username):
    if "username" not in session:
        return render_template('Login.html', message="Bạn chưa đăng nhập")
    else:
        imageCount = 0
        username = session["username"]
        image_folder = os.path.join(app.config['UPLOAD_FOLDER'], username)
        label_folder = os.path.join(app.config['UPLOAD_FOLDER'], username)
        if not os.path.exists(image_folder):
            os.makedirs(image_folder)
        imageCount = users.count_documents({'user': username, 'Type': 'Label'})
        if "username" in session:
            if request.method == 'POST':
                if 'file' not in request.files:
                    print('No file part')
                    return 'No file part'
                file = request.files['file']
                if file.filename == '':
                    print('No selected file')
                    return 'No selected file'
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    # print(imageCount)
                    if int(imageCount) < 5:
                        print(imageCount)
                        label_image = {'user': username, 'Type': 'Label','Image_name': filename,
                                       'path': os.path.join(label_folder, filename), 'coordinate': []}
                        users.insert_one(label_image)
                    # Lưu thông tin ảnh vào MongoDB
                    detect_image = {'user': username, 'Type': 'Train','Image_name': filename,
                                    'path': os.path.join(image_folder, filename)}
                    users.insert_one(detect_image)
                    file.save(os.path.join(image_folder, filename))
                return render_template('Upload.html', username=username, message="Upload thành công")
    return render_template('Upload.html', username=username)


@app.route('/ShowImage/<username>')
def show_images(username):
    if "username" not in session:
        return render_template("Login.html", username=username, message='Bạn chưa đăng nhập')
    else:
        imageCount = users.count_documents({'user': username, 'Type': 'Label'})
        if imageCount == 0:
            return render_template('ShowImage.html', username=username, message="Bạn chưa upload ảnh")
        else:
            images_list = users.find({'user':username, 'Type':'Label'})
            images = []
            for image_doc in images_list:
                image_path = image_doc['path']
                print(image_path)
                image_name = image_path.split('\\').pop()
                images.append(image_name)
            return render_template('ShowImage.html', username=username, images=images)


@app.route('/About')
def about():
    return render_template("About.html")


@app.route('/Save/<filename>')
def save(filename):
    username = session["username"]
    path = "Image/" + username + '/'
    return send_file(path + filename, as_attachment=True)


@app.route('/draw/<image_name>')
def draw(image_name):
    if 'username' in session:
        username = session['username']
        image_path = f'/static/Image/{username}/{image_name}'
        return render_template('DrawImage.html', username=username, image_path=image_path)
    return redirect(url_for('Login'))


@app.route('/save-coordinates', methods=['POST'])
def save_coordinates():
    username = session['username']
    data = request.get_json()
    image_name = data.get('imageName')
    coordinates = data.get('coordinates')
    if not image_name or not coordinates:
        return jsonify({'error': 'Invalid data'}), 400

    directory = os.path.join("Image", username)
    if not os.path.exists(directory):
        os.makedirs(directory)
    filename = os.path.join(directory, f"{image_name}.txt")
    coord_cloud = {}

    with open(filename, 'w') as f:
        for i, coord in enumerate(coordinates):
            if i % 2 == 0:
                f.write(f"{coord['class']} {coord['x']} {coord['y']} {coord['width']} {coord['height']}\n")
            else:
                coord_cloud[str(coord['class'])] = f"{coord['x'] - coordinates[i-1]['x']}_{coord['y'] - coordinates[i-1]['x']}_{coord['width']}_{coord['height']}"
    print(coord_cloud)
    coord_image = {'user': username, 'Type': 'Coordinate', 'Image_name': f"{image_name}.txt", 'path': filename}
    users.insert_one(coord_image)

    query = {"user": username, "Image_name": {"$regex": f"^{image_name}.*", "$options": "i"}, "Type": "Label"}
    new_values = {"$set": {"values": coord_cloud}}
    users.update_one(query, new_values)
    return jsonify({'message': 'Coordinates saved successfully!'}), 200


@app.route('/train_detect_field/<class_list>')
def train_detect_field(class_list):
    username = session["username"]
    class_list = class_list.split('_')
    # Create temporary folders
    origin_folder = os.path.join(app.config['TRAIN_FOLDER'], 'origin')
    train_folder = os.path.join(app.config['TRAIN_FOLDER'], 'train')
    val_folder = os.path.join(app.config['TRAIN_FOLDER'], 'val')
    model_folder = os.path.join(app.config['MODEL_FOLDER'], username)
    if not os.path.exists(origin_folder):
        os.makedirs(origin_folder)
    if not os.path.exists(train_folder):
        os.makedirs(train_folder)
    if not os.path.exists(val_folder):
        os.makedirs(val_folder)
    if not os.path.exists(model_folder):
        os.makedirs(model_folder)

    # Edit yaml file for training YOLO
    yaml_path = os.path.join(app.config['TRAIN_FOLDER'], 'data.yaml')
    with open(yaml_path) as f:
        content = yaml.safe_load(f)
    content['path'] = "Flask/" + app.config['TRAIN_FOLDER']
    content['train'] = 'train'
    content['val'] = 'val'
    content['nc'] = len(class_list)
    content['names'] = {}
    for idx, class_name in enumerate(class_list):
        content['names'][idx] = class_name
    with open(yaml_path, "w") as f:
        yaml.dump(content, f)

    # Copy original image to temporary folder
    image_list = users.find({'user': username, 'Type': 'Label'})
    ann_list = users.find({'user': username, 'Type': 'Coordinate'})
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
    images_list = users.find({'user': username, 'Type': 'Label'})
    average_values_coords = []
    for _class in class_list:
        values_coords = []
        for image in images_list.clone():
            values_coords.append(image['values'][_class])
        average_values_coords.append(find_average_value_coordinate(values_coords))

    try:
        train_yolo(yaml_path=yaml_path, runs_path=model_folder, epochs=20)
        weight_path = model_folder + "/train/weights/best.pt"
        shutil.copy(weight_path, app.config['UPLOAD_FOLDER'] + "/" + username)
    finally:
        shutil.rmtree(model_folder)
        shutil.rmtree(train_folder)
        shutil.rmtree(val_folder)
        shutil.rmtree(origin_folder)
        field_coords = [[] for _ in range(len(class_list))]  # FIX
        result_path = app.config['UPLOAD_FOLDER'] + "/" + username
        result = find_field_yolo(result_path + "/best.pt", result_path)
        for _result in result:
            for box in _result.boxes:
                x, y, w, h = box.xywh.tolist()[0]
                x = x / box.orig_shape[1]
                y = y / box.orig_shape[0]
                w = w / box.orig_shape[1]
                h = h / box.orig_shape[0]
                field_coords[int(box.cls.item())].append([x, y, w, h])
        retrieve_values_from_coordinates(app.config['UPLOAD_FOLDER'] + '/' + username, "result",
                                         field_coords, average_values_coords, classes=['0', '1'])
        return render_template("index.html", username=username)


if __name__ == "__main__":
    app.run(debug=True)
