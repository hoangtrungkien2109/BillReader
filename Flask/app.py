from flask import Flask, redirect, url_for, render_template, request, session, flash, send_file, jsonify
import os, cv2
from datetime import timedelta
from pymongo import MongoClient
from werkzeug.utils import secure_filename

app = Flask(__name__)
app._static_folder = ''
app.config['UPLOAD_FOLDER'] = 'Image'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


app.secret_key = "123"
app.permanent_session_lifetime = timedelta(minutes=5)

# Thiết lập kết nối MongoDB
# client = MongoClient('mongodb://localhost:27017/')
uri = "mongodb+srv://tnchau23823:abc13579@cluster0.fs6jd.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri)
# try:
#     client.admin.command('ping')
#     print("Pinged your deployment. You successfully connected to MongoDB!")
# except Exception as e:
#     print(e)
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


@app.route('/SignUp', methods=['GET', 'POST'])
def signup():
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
        image_folder =  os.path.join(app.config['UPLOAD_FOLDER'], username)
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
                        Label_image = {'user': username, 'Type': 'Label','Image_name':filename, 'path': os.path.join(image_folder, filename)}
                        users.insert_one(Label_image)
                    # Lưu thông tin ảnh vào MongoDB
                    Train_image = {'user': username, 'Type': 'Train','Image_name':filename, 'path': os.path.join(image_folder, filename)}
                    users.insert_one(Train_image)
                    file.save(os.path.join(image_folder, filename))
                return render_template('Upload.html', username=username, message="Upload thành công")
    return render_template('Upload.html', username=username)


@app.route('/ShowImage/<username>')
def show_images(username):
    if "username" not in session:
        return render_template("Login.html", username=username, message='Bạn chưa đăng nhập')
    else:
        imageCount = users.count_documents({'user' : username, 'Type' : 'Label'})
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

    with open(filename, 'w') as f:
        for i, coord in enumerate(coordinates):
            f.write(f"{coord['x1']},{coord['y1']},{coord['x2']},{coord['y2']}\n")
    coord_image = {'user': username, 'Type': 'Coordinate', 'Image_name': f"{image_name}.txt", 'path': filename}
    users.insert_one(coord_image)
    return jsonify({'message': 'Coordinates saved successfully!'}), 200


if __name__ == "__main__":
    app.run(debug=True)
