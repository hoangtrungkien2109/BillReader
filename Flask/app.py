from flask import Flask, redirect, url_for, render_template, request, session, flash, send_file, jsonify
import os
import base64
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
app= Flask(__name__)
app._static_folder = ''
draw_imgae=[]
app.config['UPLOAD_FOLDER'] = 'image_user'
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
    username = session['username']
    if username in session:
        if request.method == 'POST':
            user_folder = os.path.join(app.config['UPLOAD_FOLDER'], username)
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
    else:
        return render_template('index.html',message = 'Bạn chưa đăng nhập')
    # return render_template('Upload.html',username = username)

@app.route('/ShowImage/<username>')
def show_images(username):
    if username == "Guest":
        return render_template("index.html", message = 'Bạn chưa đăng nhập')
    else:
        user_folder = os.path.join(app.config['UPLOAD_FOLDER'], username)
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

@app.route('/save-drawed-image', methods=['POST'])
def save_drawed_image():
    data = request.json
    username = session['username']
    image_name = data['imageName']
    
    # Tạo đường dẫn tới thư mục lưu ảnh đã vẽ
    save_dir = os.path.join('image_user', username, 'drawedimage')
    
    # Tạo thư mục nếu chưa có
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    # Lấy dữ liệu hình ảnh từ canvas
    image_data = data['imageData']
    image_data = image_data.split(',')[1]  # Loại bỏ tiền tố data:image/png;base64
    
    # Giải mã dữ liệu base64 thành nhị phân
    image_data = base64.b64decode(image_data)
    
    # Tạo tên tệp mới và lưu vào thư mục
    save_path = os.path.join(save_dir, f'drawed_{image_name}')
    with open(save_path, 'wb') as f:
        f.write(image_data)
    
    return jsonify({'status': 'success', 'message': 'Image saved successfully!'})
with app.app_context():
    db.create_all()
if __name__=="__main__":
    app.run(debug= True)
