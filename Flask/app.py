from flask import Flask, redirect, url_for, render_template, request, session, flash, send_file, jsonify, send_from_directory
import os, cv2, json
from datetime import timedelta
from werkzeug.utils import secure_filename
from Flask.src.database import users, accounts, bills
import numpy as np
import json
import yaml
import shutil
import glob
from BillReader.corner_detector.corner_detector import detect_corner
from Flask.src.model_center import ValueDetector, BillClassifier

app = Flask(__name__)
app.secret_key = os.urandom(24)
app._static_folder = ''
app.config['UPLOAD_FOLDER'] = 'image'
app.config['TRAIN_FOLDER'] = 'training_model_temp_folder'
app.config['MODEL_FOLDER'] = 'models'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

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
    bill_images = {}
    for bill_doc in find_bill:
        billtype = bill_doc['bill_type']
        bill_types.append(billtype)
        image = users.find_one({'user': username, 'bill_type': billtype, 'type': 'train'})
        if image:
            image_filename = os.path.basename(image['path'])
            url_path = f'/static/image/{username}/{image_filename}'
            bill_images[billtype] = url_path

    if request.method == 'POST':
        if 'file' not in request.files:
            return render_template('upload.html', username=username, message="Chọn file để upload", bill_types=bill_types, bill_images=bill_images)

        file = request.files['file']
        if file.filename == '':
            return render_template('upload.html', username=username, message="Chọn file để upload", bill_types=bill_types, bill_images=bill_images)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)

            # Check for new bill type first, then existing bill type
            bill_type = request.form.get('new_bill_type') or request.form.get('bill_type')
            print(bill_type)
            if bill_type is None:
                return render_template('upload.html', username=username, message="Chọn loại hóa đơn", bill_types=bill_types, bill_images=bill_images)
            image_count = users.count_documents({'user': username, 'type': 'label', 'bill_type': bill_type})
            find_image_name = users.find_one({'user': username,'image_name': filename})
            if find_image_name:
                return render_template('upload.html', username=username, message="Ảnh đã được tải lên", bill_types=bill_types, bill_images=bill_images)
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
                file_bytes = np.frombuffer(file.read(), np.uint8)
                img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
                img_detect = detect_corner(
                    "models/corner_detector.pt",
                    img_path=img,
                    dst_path=os.path.join(image_folder, filename)
                )
                if img_detect is None:
                    cv2.imwrite(os.path.join(image_folder, filename), img)
                if not bills.find_one({'user': username, 'bill_type': bill_type}):
                    bills.insert_one({'user': username, 'bill_type': bill_type})
                    if bill_type is not None:
                        bill_types.append(bill_type)
                return render_template('upload.html', username=username, message="Upload thành công", bill_types=bill_types, bill_images=bill_images)
            except Exception as e:
                print(f"Error uploading file: {e}")
                return render_template('upload.html', username=username, message="Có lỗi xảy ra khi upload file", bill_types=bill_types, bill_images=bill_images)

    return render_template('upload.html', username=username, bill_types=bill_types, bill_images=bill_images)


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
        image_count = users.count_documents({'user': username,'bill_type': bill_type, 'type' : 'label'})
        if image_count == 0:
            return render_template('show_image.html', username=username, message="Bạn chưa upload ảnh")
        else:
            images_list = users.find({'user': username,'bill_type': bill_type, 'type' : 'label'})
            images = []
            for image_doc in images_list:
                image_path = image_doc['path']
                # print(image_path)
                image_name = image_path.split('\\').pop()
                txt_path = os.path.join(app.config['UPLOAD_FOLDER'],username, image_name.replace('.jpg', '.txt'))
                if os.path.exists(txt_path):
                    image_name_label = image_name + " (đã label)"
                else:
                    image_name_label = image_name
                images.append([image_name,image_name_label])
            # print(images)
            return render_template('show_image.html', username=username, images=images)


@app.route('/about')
def about():
    return render_template("about.html")


@app.route('/save/<filename>')
def save_image(filename):
    username = session["username"]
    path = "image/" + username + '/'
    return send_file(path + filename, as_attachment=True)


@app.route('/save_result/<filename>')
def save_result(filename):
    path = os.path.join('result')
    txt_filename = filename.split('.')[0] + '.txt'
    file_path = os.path.join(path, txt_filename)
    print(file_path)
    return send_file(file_path, as_attachment=True)


@app.route('/draw/<image_name>')
def draw(image_name):
    if 'username' in session:
        username = session['username']
        image_path = f'/static/image/{username}/{image_name}'
        bill = users.find_one({'user': username, 'image_name': image_name})
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
    find_bill_type = users.find_one({'user': username, "image_name": {"$regex": f"^{image_name}.*", "$options": "i"}})
    bill_type = find_bill_type['bill_type']
    # print(find_bill_type)
    with open(filename, 'w') as f:
        for i, coord in enumerate(coordinates):
            if i % 2 == 0:
                f.write(f"{coord['class']} {coord['x']} {coord['y']} {coord['width']} {coord['height']}\n")
            else:
                coord_cloud[str(coord['class'])] = f"{coord['x'] - coordinates[i-1]['x']}_{coord['y'] - coordinates[i-1]['y']}_{coord['width']}_{coord['height']}"
    print(coord_cloud)
    coord_image = {'user': username, 'bill_type':bill_type, 'type': 'coordinate', 'image_name': f"{image_name}.txt", 'path': filename}
    users.insert_one(coord_image)

    query = {"user": username, "image_name": {"$regex": f"^{image_name}.*", "$options": "i"}, "type": "label"}
    new_values = {"$set": {"values": coord_cloud}}
    users.update_one(query, new_values)
    return jsonify({'message': 'Coordinates saved successfully!'}), 200


@app.route('/select_bill_result/<username>')
def select_bill_result(username):
    if 'username' not in session:
        return render_template('login.html', username = username, message = 'Bạn chưa đăng nhập')
    else:
        username = session['username']
        bill_list = bills.find({'user': username})
        return render_template('select_bill_result.html', bill_list=bill_list)


@app.route('/result/<bill_type>')
def show_result(bill_type):
    if "username" not in session:
        return render_template("login.html", message='Bạn chưa đăng nhập')
    else:
        username = session['username']
        image_count = users.count_documents({'user': username,'bill_type': bill_type, 'type': 'train'})
        if image_count == 0:
            return render_template('show_result.html', username=username, message="Bạn chưa upload ảnh")
        else:
            images_list = users.find({'user': username, 'bill_type': bill_type, 'type': 'train'})
            images = []
            for image_doc in images_list:
                image_path = image_doc['path']
                print(image_path)
                image_name = image_path.split('\\').pop()
                images.append(image_name)
                print(images)
            return render_template('show_result.html', username=username, images=images)


@app.route('/train_detect_field/<bill_type>')
def train_detect_field(bill_type):
    username = session["username"]
    images_list = users.find({'user': username, 'type': 'label', 'bill_type': bill_type})
    classes = images_list[0]['values']
    print(len(classes))
    value_detector = ValueDetector(username=username, bill_type=bill_type, class_list=classes)
    value_detector.detect()
    return redirect(url_for('home'))

@app.route('/detect', methods=['POST'])
def detect():
    # Kiểm tra xem có file được gửi lên không
    if 'file' not in request.files:
        return jsonify({'message': 'No file part in the request'}), 400

    file = request.files['file']

    # Kiểm tra xem file có hợp lệ không
    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        # Lưu file một cách an toàn
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # (Chỗ này bạn có thể thêm code để xử lý ảnh, ví dụ như phát hiện hóa đơn)
        bill_type = 'Bill1'
        # Trả về kết quả cho client
        return jsonify({'message': f'Detected successfully for file: {filename} has billtype is {bill_type}'}), 200
    else:
        return jsonify({'message': 'Invalid file type'}), 400

if __name__ == "__main__":
    app.run(debug=True)
