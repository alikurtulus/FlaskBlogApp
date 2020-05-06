from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form, StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps
from werkzeug.utils import secure_filename
import os

UPLOAD_FOLDER = '/path/to/the/uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
           return f(*args, **kwargs)
        else:
            flash('You are not allowed to see this page ..','danger')  
            return redirect(url_for('login')) 
    return decorated_function



app = Flask(__name__)
app.secret_key = "flaskablog"
# We create connection between
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "flaskablog"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


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

class ArticleForm(Form):
    title = StringField('Title',validators=[validators.Length(min = 5, max= 100)])
    content = TextAreaField('Content', validators=[validators.Length(min = 10)])
    


mysql = MySQL(app)




@app.route('/')
def index():
  
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')    

@app.route('/articles')
def articles():
    cursor = mysql.connection.cursor()
    query = "SELECT * FROM articles"
    result = cursor.execute(query)
    if result > 0:
        articles = cursor.fetchall()
        return render_template('articles.html', articles = articles) 
    
    else:
        flash('Could find any article','danger')
        return render_template('articles.html')  
   

@app.route('/article/<string:id>')
def detail(id):
    cursor = mysql.connection.cursor()
    query = "Select * from articles where id = %s"
    result = cursor.execute(query,(id,))
    if result > 0:
        article = cursor.fetchone()
        return render_template('article.html', article = article)

    else:
        flash('Could not find this article ','danger')
        return render_template('article.html')


@app.route('/delete/<string:id>',methods = ['GET','DELETE'])
@login_required
def delete(id):
    cursor = mysql.connection.cursor()
    query = "SELECT * FROM articles WHERE author = %s and id= %s"
    result = cursor.execute(query,(session['username'],id,))
    if result >0:
        query2 = "DELETE FROM articles WHERE id = %s"
        cursor.execute(query2, (id,))
        mysql.connection.commit()
        cursor.close()
        flash('Successfully, Deleted an article ...','success')
        return redirect(url_for('dashboard')) 
    else:
        flash('This article does not exist or you are not allowed to delete this ...','warning')
        return redirect(url_for('index'))   
    

@app.route('/update/<string:id>',methods = ['GET','POST'])
@login_required
def update(id):
    if request.method == 'GET':
         cursor = mysql.connection.cursor()
         query = 'SELECT * FROM articles WHERE id = %s and author = %s'
         result = cursor.execute(query,(id,session['username']))
         if result == 0:
             flash('This article does not exist or you are not allowed to edit this','danger')
             return redirect(url_for('index'))
         else:
             article = cursor.fetchone()
             form = ArticleForm()
             form.title.data = article['title']
             form.content.data= article['content']
             return render_template('update.html',form = form)
    
    else:
        form = ArticleForm(request.form)
        newTitle = form.title.data
        newContent= form.content.data
        cursor = mysql.connection.cursor()
        query2 = "UPDATE articles SET title = %s , content = %s where id = %s"

        cursor.execute(query2,(newTitle,newContent,id))
        mysql.connection.commit()
        cursor.close()

        flash('Successfully ,Updated this article..','success')
        return redirect(url_for('dashboard'))

   
    



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
@login_required
def dashboard():
    cursor = mysql.connection.cursor()
    query = "SELECT * FROM articles WHERE author = %s"
    result = cursor.execute(query,(session['username'],))
    if result > 0:
        articles = cursor.fetchall()
        return render_template('dashboard.html',articles = articles)

    else:
        return render_template('dashboard.html')
    
@app.route('/addarticle', methods = ['GET','POST'])
@login_required
def addarticle():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        content = form.content.data
        cursor = mysql.connection.cursor()
        query = 'INSERT INTO articles(title,author,content) VALUES(%s,%s,%s)'
        cursor.execute(query,(title,session['username'],content))
        mysql.connection.commit()
        cursor.close()
        flash('Successfully, Added an article','success')
        return redirect(url_for('dashboard'))

    else:
        return render_template('addarticle.html', form = form)




@app.route('/search',methods =['GET','POST'])
def search():
    if request.form == 'GET':
        return redirect(url_for('index'))
    else:
        keyword = request.form.get('keyword')

        cursor =mysql.connection.cursor()

        query = "SELECT * FROM articles WHERE title LIKE '%" + keyword + "%'"
        result  = cursor.execute(query)

        if result == 0:
            flash('Could not find any result ...','warning')
            return redirect(url_for('articles'))

        else:
            articles = cursor.fetchall()
            return render_template('articles.html', articles = articles)














if __name__ == '__main__':
    app.run(debug=True)