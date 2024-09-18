from flask import Flask, redirect, url_for, render_template, request, session, flash, send_file, jsonify
import os,cv2
import base64
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
app= Flask(__name__)
app._static_folder = ''
app.config['UPLOAD_FOLDER'] = 'Flask/image_user'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

app.secret_key="123"
app.config['SQLALCHEMY_DATABASE_URI']= 'sqlite:///users.sqlite3'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"]= False
app.permanent_session_lifetime= timedelta(minutes=5)

db =SQLAlchemy(app)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False) 
    password = db.Column(db.String(80), nullable=False)
    images = db.relationship('Image', backref='user', lazy=True)

class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    path = db.Column(db.String(120), nullable=False)
    
@app.route("/")
def home():
    if 'username' in session:
        username = session['username']
    else:
        username = 'Guest'
    return render_template("index.html", username = username)

@app.route('/Login', methods=['GET', 'POST'])
def Login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        session["username"] = username
        user = User.query.filter_by(username = username).first()
        password = User.query.filter_by(password = password).first()
        if user and password:
            flash('Đăng nhập thành công!')
            return redirect('/')
        else:
            flash('Tên đăng nhập hoặc mật khẩu không đúng')
    return render_template('Login.html')

@app.route('/SignUp', methods=['GET', 'POST'])
def Signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        return render_template('SignUp.html', message='Đăng ký thành công!')
        # return redirect('/Login')
    return render_template('SignUp.html')

@app.route("/Logout")
def logout():
    session.pop("username",None)
    return render_template('Logout.html', message='Đăng xuất thành công!')

@app.route('/Upload/<username>', methods=['GET', 'POST'])
def Upload_file(username):
    imageCount = 1
    for root, dirs, files in os.walk('Flask/image_user/chau/Label'):
        imageCount += len(files)
    if 'username' in session:
        if request.method == 'POST':
            if imageCount<=5:
                user_folder = os.path.join(app.config['UPLOAD_FOLDER'], username,'Label')
            else:
                user_folder = os.path.join(app.config['UPLOAD_FOLDER'], username,'Train')
            if not os.path.exists(user_folder):
                os.makedirs(user_folder)
            if 'file' not in request.files:
                print('No file part')
                return 'No file part'
            file = request.files['file']
            if file.filename == '':
                print('No selected file')
                return 'No selected file'
            # Lưu file vào thư mục đã định
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(user_folder, filename))
                return render_template('Upload.html', username = username, message='Upload file thành công!')
    return render_template('Upload.html',username = username)

@app.route('/ShowImage/<username>')
def show_images(username):
    if username == "Guest":
        return render_template("index.html", message = 'Bạn chưa đăng nhập')
    else:
        user_folder = os.path.join(app.config['UPLOAD_FOLDER'], username,'Label')
        images = os.listdir(user_folder)
        return render_template('ShowImage.html', username = username, images = images)
    
@app.route('/About')
def About():
    return render_template("About.html")

@app.route('/Save/<filename>')
def Save(filename):
    username = session["username"]
    path = "image_user/" + username + '/'
    return send_file(path + filename, as_attachment=True)

@app.route('/draw/<image_name>')
def draw(image_name):
    if 'username' in session:
        username = session['username']
        image_path = f'/static/image_user/{username}/{image_name}'
        return render_template('DrawImage.html', image_path=image_path)
    return redirect(url_for('Login'))

@app.route('/save-coordinates', methods=['POST'])
def save_coordinates():
    username = session['username']
    data = request.get_json()
    x1 = data['x1']
    y1 = data['y1']
    x2 = data['x2']
    y2 = data['y2']
    image_name = data['imageName']

    # Đường dẫn tới thư mục chứa file tọa độ
    directory = os.path.join("Flask", "image_user_rectangle", username)
    # Kiểm tra và tạo thư mục nếu chưa tồn tại
    if not os.path.exists(directory):
        os.makedirs(directory)
    # Tên file tọa độ
    filename = os.path.join(directory, f"{image_name}.txt")
    # Ghi tọa độ vào file
    with open(filename, 'w') as f:
        f.write(f"{x1},{y1},{x2},{y2}\n")

    return "Tọa độ đã được lưu thành công!"

@app.route('/save-coordinates-test', methods=['POST'])
def save_coordinates_test():
    # Nhận dữ liệu từ client
    username=session['username']
    data = request.get_json()
    x1 = data['x1']
    y1 = data['y1']
    x2 = data['x2']
    y2 = data['y2']
    image_name = data['imageName']
    directory = os.path.join("Flask", "image_user_rectangle", username)
    # Kiểm tra và tạo thư mục nếu chưa tồn tại
    if not os.path.exists(directory):
        os.makedirs(directory)
    # Tên file tọa độ
    filename = os.path.join(directory, f"{image_name}.txt")
    # Lưu dữ liệu vào file (thay thế bằng cách lưu vào database nếu cần)
    with open(filename, 'w') as f:
        json.dump(data, f)

    return jsonify({'message': 'Tọa độ đã được lưu thành công!'})
def ve():
    with open('Flask/image_user_rectangle/chau/appli1.txt', 'r') as f:
        coords = f.readline().split(',')
        x1, y1, x2, y2 = map(float, coords)
    img = cv2.imread('Flask/image_user/chau/appli1.jpg')

    # Vẽ hình chữ nhật
    cv2.rectangle(img, (int(x1),int(y1)), (int(x2),int(y2)), (0,0,255), 1)

    # Hiển thị ảnh
    cv2.imshow("img",img) # Use cv2_imshow instead of cv2.imshow
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
with app.app_context():
    db.create_all()
if __name__=="__main__":
    app.run(debug= True)
