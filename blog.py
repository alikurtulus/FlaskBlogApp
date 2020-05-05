from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form, StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt

app = Flask(__name__)
app.secret_key = "flaskablog"
# We create connection between
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "flaskablog"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"


#Register Form
class RegisterForm(Form):
    name = StringField("Full Name",validators=[validators.Length(min = 4 , max = 25)])
    username = StringField("UserName",validators=[validators.Length(min = 5 , max = 35)])
    email = StringField("Email",validators=[validators.Length(min = 10 , max = 35),validators.Email('Plese enter a correct email address')])
    password = PasswordField("Password:",validators=[
        validators.Length(min = 6),
        validators.DataRequired(message = "Please enter a password"),
        validators.EqualTo(fieldname = "confirm",message = "Password does not match")
    ])
    confirm = PasswordField("PasswordConfirmation:")


class LoginForm(Form):
    email = StringField('Email',validators=[
        validators.Length(min= 4, max = 25),
        validators.Email('Please enter correct email ...'),
        validators.DataRequired(message = 'Please enter an email ...')
        ])
    password = PasswordField('Password',validators=[
        validators.Length(min = 4, max = 25),
        validators.DataRequired(message='Please enter a password')
    ])    

mysql = MySQL(app)




@app.route('/')
def index():
  
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')    

@app.route('/articles')
def articles():
    return render_template('articles.html')

@app.route('/article/<string:id>')
def detail(id):
    return "Article Id :" + id

@app.route('/register',methods = ['GET','POST'])
def register():

    form = RegisterForm(request.form)

    if request.method == "POST" and form.validate():
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)
        cursor = mysql.connection.cursor()
        query = "INSERT INTO users(name,email,username,password) VALUES(%s,%s,%s,%s)"
        cursor.execute(query,(name,email,username,password))

        mysql.connection.commit()

        cursor.close()
        flash("Succesfuly Signed Up!!","success")
        return redirect(url_for('login'))

    else:
        return render_template('register.html',form = form)

@app.route('/login',methods=['GET','POST'])
def login():
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        email = form.email.data
        password_entered = form.password.data

        cursor = mysql.connection.cursor()
        query = "SELECT * FROM users WHERE email= %s"

        result = cursor.execute(query,(email,))

        if result > 0:
            data = cursor.fetchone()
            real_password = data['password']
            username = data['username']
            if sha256_crypt.verify(password_entered,real_password):
                flash('Succesfully login','success')
                session['logged_in'] = True
                session['username'] = username
                return redirect(url_for('index'))
            else:
                flash('Invalid inputs','danger')
                return redirect(url_for('login'), form = form)


        else:
            flash('This user does not exist ...', 'danger')
            return redirect(url_for('login'))

    else:
        return render_template('login.html', form = form)



@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')
    


if __name__ == '__main__':
    app.run(debug=True)