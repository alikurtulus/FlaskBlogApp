from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form, StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt

app = Flask(__name__)

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

        return redirect(url_for('index'))

    else:
        return render_template('register.html',form = form)


if __name__ == '__main__':
    app.run(debug=True)