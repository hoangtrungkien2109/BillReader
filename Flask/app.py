from flask import Flask, redirect, url_for, render_template, request, session, flash, send_file, jsonify
import os, cv2
from datetime import timedelta
from werkzeug.utils import secure_filename
# from Flask.database import db, users, accounts, bills
import numpy as np
import yaml
import shutil
# from BillReader.utils import multiprocess_augment
# from BillReader.bill_classifier.bill_classifier_model import train_classifier_model, classify_image
# from BillReader.corner_detector.corner_detector import detect_corner
# from BillReader.field_detector.value_extractor import (retrieve_values_from_coordinates, find_value_coordinate,
#                                                        detect_value_box, get_value_coordinates_from_annotation_file,
#                                                        find_field_yolo, train_yolo, extract_bill_from_image,
#                                                        split_field_value_from_annotation, find_average_value_coordinate)

app = Flask(__name__)
app.secret_key = os.urandom(24)
app._static_folder = ''
app.config['UPLOAD_FOLDER'] = 'Flask/image'
app.config['TRAIN_FOLDER'] = 'training_model_temp_folder'
app.config['MODEL_FOLDER'] = 'models'
from pymongo import MongoClient

uri = "mongodb+srv://hoangtrungkien4:R22QsguGNpBfTHlw@billreader.kc3jt.mongodb.net/?retryWrites=true&w=majority&appName=BillReader"
client = MongoClient(uri)

db = client['my_database']
accounts = db['account']
users = db['user']
bills = db['bill']

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
# bill_types=['Bill1','Bill2','Bill3']


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


app.permanent_session_lifetime = timedelta(minutes=100)


@app.route("/")
def home():
    if "username" in session:
        username = session["username"]
    else:
        username = 'guest'
    return render_template("index.html", username=username)


@app.route('/login', methods=['GET', 'POST'])
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
            return render_template('login.html',message='Tên đăng nhập hoặc mật khẩu không đúng')
    return render_template('login.html')


@app.route('/sign_up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Thêm người dùng mới vào MongoDB
        if accounts.find_one({'username': username}):
            return render_template('sign_up.html', message='Tài khoản đã tồn tại')
        else:
            new_user = {'username': username, 'password': password}
            accounts.insert_one(new_user)
            return render_template('sign_up.html', message='Đăng ký thành công!')
    return render_template('sign_up.html')


@app.route("/logout")
def logout():
    session.pop("username", None)
    return render_template('login.html', message='Đăng xuất thành công!')


@app.route('/upload/<username>', methods=['GET', 'POST'])
def upload_file(username):
    if "username" not in session:
        return render_template('login.html', message="Bạn chưa đăng nhập")
    username = session["username"]

    find_bill = bills.find({'user': username})
    bill_types = []
    for bill_doc in find_bill:
        billtype = bill_doc['bill_type']
        bill_types.append(billtype)
    print(bill_types)
    if request.method == 'POST':
        if 'file' not in request.files:
            return render_template('upload.html', username=username, message="Chọn file để upload", bill_types=bill_types)

        file = request.files['file']
        if file.filename == '':
            return render_template('upload.html', username=username, message="Chọn file để upload", bill_types=bill_types)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)

            # Check for new bill type first, then existing bill type
            bill_type = request.form.get('new_bill_type') or request.form.get('bill_type')
            if bill_type is None:
                return render_template('upload.html', username=username, message="Chọn loại hóa đơn", bill_types=bill_types)
            image_count = users.count_documents({'user': username, 'type': 'label', 'bill_type': bill_type})
            find_image_name = users.find_one({'user': username,'image_name' : filename})
            if find_image_name:
                return render_template('upload.html', username=username, message="Ảnh đã được tải lên", bill_types=bill_types)
            if image_count < 5:
                label_image = {
                'user': username,
                'bill_type': bill_type,
                'type': 'label',
                'image_name': filename,
                'path': os.path.join(app.config['UPLOAD_FOLDER'], username, filename),
                'coordinate': []
                }
                users.insert_one(label_image)
            train_image = {
                'user': username,
                'bill_type': bill_type,
                'type': 'train',
                'image_name': filename,
                'path': os.path.join(app.config['UPLOAD_FOLDER'], username, filename)
            }
            users.insert_one(train_image)
            image_folder = os.path.join(app.config['UPLOAD_FOLDER'], username)
            if not os.path.exists(image_folder):
                os.makedirs(image_folder)
            try:
                file.save(os.path.join(image_folder, filename))
                if not bills.find_one({'user': username, 'bill_type': bill_type}):
                    bills.insert_one({'user': username, 'bill_type': bill_type})
                    if bill_type != None:
                        bill_types.append(bill_type)
                return render_template('upload.html', username=username, message="Upload thành công", bill_types=bill_types)
            except Exception as e:
                print(f"Error uploading file: {e}")
                return render_template('upload.html', username=username, message="Có lỗi xảy ra khi upload file", bill_types=bill_types)

    return render_template('upload.html', username=username, bill_types=bill_types)

@app.route('/select_bill/<username>')
def select_bill(username):
    if "username" not in session:
        return render_template("login.html", username=username, message='Bạn chưa đăng nhập')
    else:
        username = session["username"]
        bill_list = bills.find({'user': username})
        return render_template('select_bill.html', bill_list=bill_list)


@app.route('/bill/<bill_type>')
def show_image(bill_type):
    if "username" not in session:
        return render_template("login.html", message='Bạn chưa đăng nhập')
    else:
        username = session['username']
        image_count = users.count_documents({'user' : username,'bill_type': bill_type, 'type' : 'label'})
        if image_count == 0:
            return render_template('show_image.html', username=username, message="Bạn chưa upload ảnh")
        else:
            images_list = users.find({'user' : username,'bill_type': bill_type, 'type' : 'label'})
            images = []
            for image_doc in images_list:
                image_path = image_doc['path']
                print(image_path)
                image_name = image_path.split('\\').pop()
                images.append(image_name)
                print(images)
            return render_template('show_image.html', username=username, images=images)


@app.route('/about')
def about():
    return render_template("about.html")


@app.route('/save/<filename>')
def save_image(filename):
    username = session["username"]
    path = "image/" + username + '/'
    return send_file(path + filename, as_attachment=True)


@app.route('/draw/<image_name>')
def draw(image_name):
    if 'username' in session:
        username = session['username']
        image_path = f'/static/image/{username}/{image_name}'
        bill = users.find_one({'image_name': image_name})
        bill_type = bill['bill_type']  # Giả sử BillType nằm trong trường 'BillType' của bill
        return render_template('draw_image.html', username=username,bill_type=bill_type, image_path=image_path)
    return redirect(url_for('login'))


@app.route('/save-coordinates', methods=['POST'])
def save_coordinates():
    username = session['username']
    data = request.get_json()
    image_name = data.get('image_name')
    coordinates = data.get('coordinates')
    if not image_name or not coordinates:
        return jsonify({'error': 'Invalid data'}), 400

    directory = os.path.join(app.config['UPLOAD_FOLDER'], username)
    if not os.path.exists(directory):
        os.makedirs(directory)
    filename = os.path.join(directory, f"{image_name}.txt")
    # print(filename)
    coord_cloud = {}
    find_bill_type = users.find_one({'user':username,"image_name": {"$regex": f"^{image_name}.*", "$options": "i"}})
    bill_type = find_bill_type['bill_type']
    # print(find_bill_type)
    with open(filename, 'w') as f:
        for i, coord in enumerate(coordinates):
            if i % 2 == 0:
                f.write(f"{coord['class']} {coord['x']} {coord['y']} {coord['width']} {coord['height']}\n")
            else:
                coord_cloud[str(coord['class'])] = f"{coord['x'] - coordinates[i-1]['x']}_{coord['y'] - coordinates[i-1]['x']}_{coord['width']}_{coord['height']}"
    print(coord_cloud)
    coord_image = {'user': username, 'bill_type':bill_type, 'type': 'coordinate', 'image_name': f"{image_name}.txt", 'path': filename}
    users.insert_one(coord_image)

    query = {"user": username, "image_name": {"$regex": f"^{image_name}.*", "$options": "i"}, "type": "label"}
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
    image_list = users.find({'user': username, 'type': 'label'})
    ann_list = users.find({'user': username, 'type': 'coordinate'})
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
    images_list = users.find({'user': username, 'type': 'label'})
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
