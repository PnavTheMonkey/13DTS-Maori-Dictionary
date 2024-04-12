from flask import Flask, render_template, redirect, request  #imports the neccesary modules from Flask
import sqlite3
from sqlite3 import Error

DATABASE ='./database.db'
app = Flask(__name__)


def create_connection(db_file):
    try:
        connection = sqlite3.Connection(db_file)
        return connection
    except Error as e:
        print(e)
    return None

@app.route('/')
def render_homepage():
    return render_template('home.html')
    print("ssss")

@app.route('/login', methods=['POST', 'GET'])
def render_login():
    return render_template('login.html')

@app.route('/signup', methods=['POST', 'GET'])
def render_signup():
    if request.method == 'POST':
        print(request.form)
        fname = request.form('fname').title().strip()
        lname = request.form.get('lname').title().strip()
        email = request.form.get('email').lower().strip()
        password = request.form.get('password')
        password2 = request.form.get('password2')

        if password != password2:
            return redirect("/signup?error='Passwords do not match.")
        if len(password) < 8:
            return redirect("/signup?error='Password must be at least 8 characters.")

        con = open_database(DATABASE)
        query = "INSERT INTO users (fname, lname, email, password) VALUES (?,?,?,?)"
        cur = con.cursor()

        try:
            cur.execute(query, (fname, lname, email, password))
        except sqlite3.IntegrityError:
            con.close()
            return r edirect("/signup?error='Email is already in use.")

        con.commit()
        con.close()

        return redirect("/login")



    return render_template('/signup.html')

app.run(host='0.0.0.0', debug=True)


   