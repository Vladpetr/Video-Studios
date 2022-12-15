from flask import Flask, render_template, request, session
import rds as db

app = Flask(__name__)

@app.route("/")
def index():
    return render_template('index.html')


@app.route('/signup', methods=['post'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        db.insert_details(name,email,password)
        msg = "Registration Complete. Please log in to your account"
    
        return render_template('login.html', msg = msg)
    return render_template('index.html')

@app.route('/login')
def login():    
    return render_template('login.html')

@app.route('/check',methods = ['post'])
def check():
    if request.method=='POST':
        email = request.form['email']
        password = request.form['password']
        db.conn.cursor.execute('SELECT * FROM Users WHERE email = % s AND password = % s', (email, password))
        account = db.conn.cursor.fetchone()
        if account:
            name = account["name"]
            return render_template("home.html", name = name)
        else:
            msg = 'Incorrect username or password.'
    return render_template("login.html", msg=msg)

@app.route('/home')
def home():
    return render_template('home.html')


if __name__ == "__main__":
    app.run()