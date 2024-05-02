from flask import Flask, render_template, request ,redirect, url_for, session
from flask import  flash
from flask_login import LoginManager

from flask_mysqldb import MySQL
import MySQLdb.cursors
from flask_login import logout_user
import re
import pickle
import sys
import os
import glob
import re
import numpy as np
from pprint import pprint
from flask import flash
import bcrypt

# Keras
from keras.applications.vgg16 import preprocess_input
from keras.models import load_model
from keras.preprocessing import image

# Flask utils
from werkzeug.utils import secure_filename

app = Flask(__name__)

app.secret_key = 'super secret key'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'prediction'
 
mysql = MySQL(app)


@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST':
        # Fetch form data
        email = request.form['email']
        password = request.form['password']

        # Fetch user from database
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cursor.fetchone()
        if user:
            # Check if password matches hashed password
            if bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
                # Passwords match, redirect to dashboard or home page
                session['loggedin'] = True
                session['id'] = user['id']
                session['username'] = user['username']
                session['type'] = user['type']
                flash('Login successful!', 'success')
                return redirect(url_for('home'))  # Change 'dashboard' to your actual dashboard route
            else:
                msg = 'Incorrect password.'
        else:
            msg = 'User not found.'

    return render_template('login.html', msg=msg)



@app.route('/doctorLogin', methods =['GET', 'POST'])
def doctorLogin():
    msg = ''
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM doctors WHERE email = % s', (email, ))
        user = cursor.fetchone()
        if user:
            # Check if password matches hashed password
            if bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
                # Passwords match, redirect to dashboard or home page
                session['loggedin'] = True
                session['id'] = user['id']
                session['username'] = user['username']
                return redirect(url_for('doctor_home'))  # Change 'dashboard' to your actual dashboard route
            else:
                msg = 'Incorrect password.'
        else:
            msg = 'User not found.'

    return render_template('doctorLogin.html', msg=msg)

@app.route('/logout', methods=['GET'])
def logout():
    if 'loggedin' in session:
        # Clear the user's session
        session.clear()
        flash('You have been successfully logged out.', 'success')
    else:
        flash('You are not logged in.', 'info')
    # Redirect the user to the home page
    return redirect(url_for('home'))

@app.route('/register', methods =['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form and 'type' in request.form and 'address' in request.form and 'phone' in request.form and 'sex' in request.form:
        username = request.form['username']
        if username:
         usernamee = username.replace(" ", "_")
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        email = request.form['email']
        address = request.form['address']
        phone = request.form['phone']
        sex = request.form['sex']
        type = request.form['type']
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE username = % s', (usernamee, ))
        account = cursor.fetchone()
        if account:
            msg = 'Account already exists !'
        if password != confirm_password:
            msg='Passwords do not match. Please try again.'    
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address !'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers !'
        elif not username or not password or not email:
            msg = 'Please fill out the form !'
        else:
            cursor.execute('INSERT INTO users VALUES (NULL, % s,% s, % s, % s, % s, % s, % s)', (usernamee,type, hashed_password, email,address,phone,sex ))
            mysql.connection.commit()
            account = cursor.fetchone()
            return redirect(url_for('login'))
            msg = 'You have successfully registered !'
    elif request.method == 'POST':
        msg = 'Please fill out the form !'
    return render_template('register.html', msg = msg)


@app.route('/update_user', methods=['POST'])
def update_user():
    # Fetch form data
    user_id = request.form['user_id']
    username = request.form['username']
    if username:
         usernamee = username.replace(" ", "_")
    address = request.form['address']
    phone = request.form['phone']

    # Validate inputs
    if not all([user_id, username,  address]):
        return 'Please fill out all the fields.'
    elif not re.match(r'[A-Za-z0-9]+', username):
        return 'Username must contain only characters and numbers.'

    # Update user information in the database
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('UPDATE users SET username = %s,address = %s ,phone = %s  WHERE id = %s',
                   (usernamee,  address,phone, user_id))
    mysql.connection.commit()

    return redirect(url_for('profile'))


@app.route('/update_doctor', methods=['POST'])
def update_doctor():
    # Fetch form data
    user_id = request.form['user_id']
    username = request.form['username']
    if username:
         usernamee = username.replace(" ", "_")
    address = request.form['address']
    city = request.form['city']
    price = request.form['price']

    # Validate inputs
    if not all([user_id, username, address,city,address,price]):
        return 'Please fill out all the fields.'
    elif not re.match(r'[A-Za-z0-9]+', username):
        return 'Username must contain only characters and numbers.'

    # Update user information in the database
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('UPDATE doctors SET username = %s, address = %s, city = %s ,price = %s WHERE id = %s',
                   (usernamee, address,city,price, user_id))
    mysql.connection.commit()

    return redirect(url_for('doctor_home'))


@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    msg = ''
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        old_password = request.form['old_password']
        new_password = request.form['new_password']

        # Fetch user from database
        user_id = session['id']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))
        user = cursor.fetchone()
        
        # Check if old password matches
        if bcrypt.checkpw(old_password.encode('utf-8'), user['password'].encode('utf-8')):
            # Validate new password
            if len(new_password) < 8:
                msg='New password must be at least 8 characters long.'
            else:
                # Update password in database
                hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
                cursor.execute('UPDATE users SET password = %s WHERE id = %s', (hashed_password, user_id))
                mysql.connection.commit() 
                msg='Password changed successfully.'
                return redirect(url_for('profile'))
        else:
            msg='Incorrect old password.'

    return render_template('change_password.html',msg=msg)










@app.route('/doctorRegister', methods =['GET', 'POST'])
def doctorRegister():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form and 'address' in request.form and 'spec' in request.form and 'city' in request.form and 'price' in request.form and 'sex' in request.form:
        username = request.form['username']
        if username:
         usernamee = username.replace(" ", "_")
        password = request.form['password']
        email = request.form['email']
        city = request.form['city']
        address = request.form['address']
        spec = request.form['spec']
        price = request.form['price']
        sex = request.form['sex']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        cursor.execute('SELECT * FROM doctors WHERE username = % s', (usernamee, ))
        account = cursor.fetchone()
        if account:
            msg = 'Account already exists !'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address !'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers !'
        elif not username or not password or not email:
            msg = 'Please fill out the form !'
        else:
            cursor.execute('INSERT INTO doctors VALUES (NULL, % s,% s, % s, % s,% s,% s,% s,% s)', (usernamee, hashed_password, email,city,address,spec,price,sex ))
            mysql.connection.commit()
            account = cursor.fetchone()
            return redirect(url_for('doctorLogin'))
            msg = 'You have successfully registered !'
    elif request.method == 'POST':
        msg = 'Please fill out the form !'
    return render_template('doctorRegister.html', msg = msg)


@app.route("/contact_us", methods =['GET', 'POST'])
def contact_us():
    if request.method == 'POST' and 'name' in request.form and 'email' in request.form and 'subject' in request.form and 'message' in request.form:
        name = request.form['name']
        email = request.form['email']
        subject = request.form['subject']
        message = request.form['message']

        mysql.connection.commit() 
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)  
        cursor.execute('INSERT INTO contact VALUES (NULL, % s,% s, % s, % s)', (name, email, subject,message ))
        mysql.connection.commit()
        flash("Your message has been successful")
        return redirect(url_for('home'))   
      














suger_model = pickle.load(open('suger.pkl', 'rb'))

MODEL_PATH = 'models/trained_model.h5'
model = load_model(MODEL_PATH)


@app.route("/")
@app.route("/home")
def home():
    return render_template('home.html')

 
@app.route('/chat')
def chat():
    return render_template('chat.html')
 
 
@app.route('/edit_user')
def edit_user():
    id = request.args.get('id') 
    def user():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        select_stmt = "select * FROM users WHERE id = %(id)s"
        cursor.execute(select_stmt, { 'id': id })
        user=cursor.fetchone()
        return user 
    user=user()
    return render_template('edit_user.html',id=id,user=user)

@app.route('/edit_doctor')
def edit_doctor():
    id = request.args.get('id') 
    def doctor():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        select_stmt = "select * FROM doctors WHERE id = %(id)s"
        cursor.execute(select_stmt, { 'id': id })
        doctor=cursor.fetchone() 
        return doctor 
    doctor=doctor()
    return render_template('edit_doctor.html',id=id,doctor=doctor)



 
@app.route('/make_reservation')
def make_reservation():
    id_value = request.args.get('id')  
    return render_template('make_reservation.html',id=id_value)
 

@app.route("/home")
def myhome():
    return render_template('home.html')


@app.route("/doctor_home")
def doctor_home():
    
    id=int(session['id'])
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    select_stmt = "SELECT * FROM reservations where doctor_id = %(id)s ORDER BY id DESC "
    cursor.execute(select_stmt, { 'id': id })
    mysql.connection.commit() 
    reservations=cursor.fetchall()
    def doctor():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        select_stmt = "select * FROM doctors WHERE id = %(id)s"
        cursor.execute(select_stmt, { 'id': id })
        doctor=cursor.fetchone() 
        return doctor 
    doctor=doctor()
    def users():
        select_stmt = "SELECT * FROM users"
        cursor.execute(select_stmt)
        users=cursor.fetchall() 
        return users

    users=users() 
    return render_template('doctor_home.html',reservations=reservations,users=users,doctor=doctor)



@app.route("/contact")
def contact():
    return render_template('contact.html')

@app.route("/test")
def test():
    return render_template('test.html')

@app.route("/find_doctor")
def find_doctor():
    def Getdoctors():      
     id=int(session['id'])
     cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
     select_stmt = "SELECT * FROM users where id = %(id)s ORDER BY id DESC "
     cursor.execute(select_stmt, { 'id': id })
 
     account = cursor.fetchone()
     if account:
     
      session['address'] = account['address']
     
     address=session['address']
     cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
     cursor.execute('SELECT * FROM doctors WHERE city = % s', (address, ))
 
     mysql.connection.commit() 
     Getdoctors=cursor.fetchall() 
     return Getdoctors
     
    doctors = Getdoctors()
    return render_template('find_doctor.html',doctors=doctors)
    
    
    
@app.route("/contacts")
def contacts():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    select_stmt = "SELECT * FROM contact "
    cursor.execute(select_stmt)
    contacts=cursor.fetchall()     
    return render_template('contacts.html',contacts=contacts)

    
@app.route('/delete/<int:id>', methods = ['GET','POST','DELETE'])
def contact_delete(id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    select_stmt = "DELETE FROM contact WHERE id = %(id)s ORDER BY id DESC "
    cursor.execute(select_stmt, { 'id': id })
    mysql.connection.commit() 
    return redirect(url_for('contacts'))   
      
            
@app.route("/reservation", methods =['GET', 'POST'])
def reservation():
    if request.method == 'POST' and 'user_id' in request.form and 'doctor_id' in request.form and 'date' in request.form and 'message' in request.form:
        user_id = request.form['user_id']
        doctor_id = request.form['doctor_id']
        date = request.form['date']
        message = request.form['message']

        mysql.connection.commit() 
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)  
        cursor.execute('INSERT INTO reservations VALUES (NULL, % s,% s, % s, % s)', (user_id, doctor_id, date,message ))
        mysql.connection.commit()
        flash("Your reservation has been successful")
        return redirect(url_for('find_doctor'))   
      
@app.route('/reservation_delete/<int:id>', methods = ['GET','POST','DELETE'])
def reservation_delete(id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    select_stmt = "DELETE FROM reservations WHERE id = %(id)s ORDER BY id DESC "
    cursor.execute(select_stmt, { 'id': id })
    mysql.connection.commit() 
    return redirect(url_for('doctor_home'))
 
     
@app.route('/delete_Pneumonia/<int:id>/<string:image_path>', methods = ['GET','POST','DELETE'])
def delete_Pneumonia(id,image_path):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    select_stmt = "DELETE FROM prediction_pneumonia WHERE id = %(id)s ORDER BY id DESC "
    cursor.execute(select_stmt, { 'id': id })
    mysql.connection.commit()
    imagepath = 'static/uploads/' + image_path
    if os.path.exists(imagepath):
        os.remove(imagepath)
    return redirect(url_for('pneumonia'))
 
     

   
@app.route("/profile")
def profile():
    id=int(session['id'])
    def user():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        select_stmt = "select * FROM users WHERE id = %(id)s"
        cursor.execute(select_stmt, { 'id': id })
        user=cursor.fetchone()
        return user 
    user=user()
    def Getpredictions():
     cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
     select_stmt = "SELECT * FROM prediction_suger where user_id = %(id)s ORDER BY id DESC "
     cursor.execute(select_stmt, { 'id': id })
 
     mysql.connection.commit() 
     predictions=cursor.fetchall() 
     return predictions
     
    predictions = Getpredictions()
    
    return render_template('profile.html',predictions=predictions,user=user)

@app.route("/admin")
def admin():
    def Getpredictionss():
     cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
     select_stmt = "SELECT * FROM prediction_suger ORDER BY id DESC "
     cursor.execute(select_stmt)
 
     mysql.connection.commit() 
     predictions=cursor.fetchall() 
     return predictions
     
    predictions = Getpredictionss()
    return render_template('admin.html',predictions=predictions)

@app.route('/delete_suger/<int:id>', methods = ['GET','POST','DELETE'])
def delete_suger(id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    select_stmt = "DELETE FROM prediction_suger WHERE id = %(id)s ORDER BY id DESC "
    cursor.execute(select_stmt, { 'id': id })
    mysql.connection.commit() 
    return redirect(url_for('profile'))





@app.route("/suger")
def suger():
    return render_template('suger.html')

UPLOADS_FOLDER = 'uploads'

@app.route("/pneumonia")
def pneumonia():
    id=int(session['id'])
    def Getpredictions():
     cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
     select_stmt = "SELECT * FROM prediction_pneumonia where user_id = %(id)s ORDER BY id DESC "
     cursor.execute(select_stmt, { 'id': id })
 
     mysql.connection.commit() 
     predictions=cursor.fetchall() 
     return predictions
     
    predictions = Getpredictions()
    image_files = os.listdir(UPLOADS_FOLDER)

    return render_template('pneumonia.html',predictions=predictions, image_files=image_files)

@app.route("/allpneumonias")
def allpneumonias():
     cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
     select_stmt = "SELECT * FROM prediction_pneumonia "
     cursor.execute(select_stmt)
 
     mysql.connection.commit() 
     allpneumonias=cursor.fetchall() 
     image_files = os.listdir(UPLOADS_FOLDER)

     return render_template('allpneumonia.html',allpneumonias=allpneumonias, image_files=image_files)
     
   







@app.route("/reconmendation")
def reconmendation():
    return render_template('reconmendation.html')

@app.route("/reconmendationsuger")
def reconmendationsuger():
    return render_template('reconmendationsuger.html')



@app.route("/predict_suger", methods=['POST'])
def predict_suger():
    msg=''
    Pregnancies= int(request.form['Pregnancies'])
    Glucose = int(request.form['Glucose'])
    BloodPressure = int(request.form['BloodPressure'])
    SkinThickness = int(request.form['SkinThickness'])
    Insulin = int(request.form['Insulin'])
    BMI = float(request.form['BMI'])
    DiabetesPedigreeFunction = float(request.form['DiabetesPedigreeFunction'])
    Age= int(request.form['Age'])
    
    if Age < 10 or Age > 100:
        return render_template('error.html', message='Age must be between 10 and 100')

    if Insulin < 0 or Insulin > 500:
        return render_template('error.html', message='Insulin must be between 0 and 500')

    prediction = suger_model.predict([[
        Pregnancies, Glucose,BloodPressure,SkinThickness,
        Insulin,BMI,DiabetesPedigreeFunction,Age
        ]])
    
    if request.method == 'POST' and 'Pregnancies' in request.form and 'Glucose' in request.form and 'BloodPressure' in request.form and 'SkinThickness' in request.form and 'Insulin' in request.form and 'Insulin' in request.form and 'BMI' in request.form and 'DiabetesPedigreeFunction' in request.form and 'Age' in request.form and 'user_id' in request.form :
        Pregnancies = int(request.form['Pregnancies'])
        Glucose = int(request.form['Glucose'])
        BloodPressure = int(request.form['BloodPressure'])
        SkinThickness = int(request.form['SkinThickness'])
        Insulin = int(request.form['Insulin'])
        BMI = float(request.form['BMI'])
        
        DiabetesPedigreeFunction = float(request.form['DiabetesPedigreeFunction'])
        Age =int( request.form['Age'])
        
        user_id=int(request.form['user_id'])
        result=int(prediction)
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('INSERT INTO prediction_suger VALUES (NULL, % s, % s, % s , % s , % s , % s , % s , % s , % s , % s )', (user_id, Pregnancies, Glucose, BloodPressure, SkinThickness, Insulin, BMI, DiabetesPedigreeFunction, Age, result ))
        mysql.connection.commit() 

    if(prediction==0):

            return render_template('suger.html',prediction_text=f'0')
    elif(prediction==1):
            return render_template('suger.html',prediction_text=f'1')
            

    
       
        


def model_predict(img_path, model):
    img = image.load_img(img_path, target_size=(64, 64)) #target_size must agree with what the trained model expects!!

    # Preprocessing the image
    img = image.img_to_array(img)
    img = np.expand_dims(img, axis=0)

   
    preds = model.predict(img)
    return preds


# @app.route('/predict', methods=['GET', 'POST'])
# def upload():
#     if request.method == 'POST':
#         # Get the file from post request
#         f = request.files['file']
        
#         # Save the file to ./uploads
#         basepath = os.path.dirname(__file__)
#         file_path = os.path.join(
#             basepath, 'uploads', secure_filename(f.filename))
#         f.save(file_path)

#         # Make prediction
#         preds = model_predict(file_path, model)

#         # Arrange the correct return according to the model. 
# 		# In this model 1 is Pneumonia and 0 is Normal.
    
#         str1 = 'Pneumonia.  '
#         str2 = 'Normal'
#         if preds == 1:
          
#             return str1
#         else:
#             return str2




import numpy as np
from tensorflow.keras.models import load_model
from flask import Flask, render_template, request
import time


@app.route('/predict_pneumonia', methods=['POST'])
def predict_pneumonia():
    if 'image' not in request.files:
        return 'No image uploaded'
    user_id=request.form['id']
    img = request.files['image']
    timestamp = str(time.time())
    # Perform pneumonia detection
    basepath = os.path.dirname(__file__)
    file_path = os.path.join(
        basepath, 'static/uploads', secure_filename(timestamp+img.filename))
    img.save(file_path)
    
        # Make prediction
        
    result = model_predict(file_path, model)

    cursor = mysql.connection.cursor()
    cursor.execute('INSERT INTO prediction_pneumonia (id,user_id,image_path, has_pneumonia) VALUES (Null,%s,%s, %s)', (user_id,timestamp+img.filename, result))
    mysql.connection.commit()
    
    if result > 0.5:
        return render_template('test.html',result=f'1')
    else:
        return render_template('test.html',result=f'0')
 










    #this section is used by gunicorn to serve the app on Heroku
if __name__ == '__main__':
        app.run(use_reloader=True)


