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



app.run(host='0.0.0.0', debug=True)


   