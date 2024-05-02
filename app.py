from flask import Flask, render_template, redirect, request  #imports the neccesary modules from Flask
import sqlite3
from sqlite3 import Error
#from flask_bcrypt import Bcrypt


DATABASE ='./database.db'   # Define the path to the SQLite database file

app = Flask(__name__)    # Create a Flask application instance
bcrypt = Bcrypt(app)    ## Initialize Bcrypt with the Flask application
app.secret_key = "uhb*#189hpaqey "    # Set a secret key for the Flask application this is the key for hashed password


def create_connection(db_file):       # Function to create a connection to the SQLite database
    try:
        connection = sqlite3.Connection(db_file)       # Attempt to establish a connection to the SQLite database
        return connection
    except Error as e:
        print(e)           # Print an error message if connection fails
    return None

def is_logged_in(): # Function to check if user is logged in
    if session.get("email") is None:
        print("not logged in ")         # Print message if user is not logged in
        return False
    else:
        print("logged in!")         # Print message if user is logged in
        return True
@app.route('/')
def render_homepage():     # Render the home.html template
    return render_template('home.html')      # This print statement will not be executed as it comes after the return statement
    print("home")

@app.route('/login', methods=['POST', 'GET'])
def render_login():
    if is_logged_in():      # Check if user is already logged in
        return redirect('/menu/1')
    if request.method == "POST":         # Extract email and password from the form
        email = request.form['email'].strip().lower()
        password = request.form['password'].strip()

        query = """SELECT id, fname, password FROM user WHERE email = ?"""       # Query to fetch user data from the database
        con = create_connection(DATABASE)         # Create a connection to the database
        cur = con.cursor()
        cur.execute(query, (email, ))
        user_data = cur.fetchone()         # Fetch user data
        con.close()

        try:
            user_id = user_data[0]             # Extract user_id, first_name, and db_password from user_data
            first_name = user_data[1]
            db_password = user_data[2]
        except IndexError:
            return redirect("/login?error=Invalid+username+or+password")        # Redirect to login page with an error message if user does not exist
        if not bcrypt.check_password_hash(db_password, password):         # Check if the provided password matches the hashed password stored in the database
            return redirect(request.referrer + '?error=Email+invalid+or+password+incorrect')        # Redirect to the previous page with an error message if password is incorrect

        # Create session variables
        session['email'] = email
        session['userid'] = user_id
        session['firstname'] = first_name
        print(session)
        return redirect('/')
    return render_template("login.html", logged_in = is_logged_in())      # Render the login page for GET requests

@app.route('/dictionary/<cat_id>')
def render_menu_page(cat_id):
    con = create_connection(DATABASE)      # Create a connection to the SQLite database
    query = "SELECT name, description, volume, image, price FROM products WHERE cat_id=?"    # Define the SQL query to fetch products based on cat_id
    cur = con.cursor()
    cur.execute(query, (cat_id, ))     # Execute the SQL query
    dictionary_list = cur.fetchall()     # Fetch all the products

    dictionary_list = cur.fetchall()
    query = "SELECT id, name FROM category"
    cur = con.cursor()
    cur.execute(query)
    categories_list = cur.fetchall()      # Fetch categories
    con.close()
    print(dictionary_list)  # Print the fetched dictionary_list
    return render_template('dictionary.html', products=dictionary_list, categories=categories_list)      # Render the dictionary.html template with the fetched data


@app.route('/signup', methods=['POST', 'GET'])
def render_signup():
    if request.method == 'POST':
        print(request.form)
        fname = request.form.get('fname').title().strip()   # Extract form data
        lname = request.form.get('lname').title().strip()
        email = request.form.get('email').lower().strip()
        password = request.form.get('password')
        password2 = request.form.get('password2')

        if password != password2:            # Check if passwords match
            return redirect("\signup?error='Passwords+do+not+match")
        if len(password) < 8:         # Check if password is at least 8 characters long
            return redirect("\signup?error='Password+must+be+at+least+8+characters")

        hashed_password = bcrypt.generate_password_hash(password)         # Hash the password
        con = open_database(DATABASE)        # Open a connection to the database
        query = "INSERT INTO users (fname, lname, email, password) VALUES (?,?,?,?)"
        cur = con.cursor()

        try:
            cur.execute(query, (fname, lname, email, hashed_password))
        except sqlite3.IntegrityError:
            con.close()
            return redirect("\signup?error='Email is already in use.")

        con.commit()         # Commit changes and close connection
        con.close()

        return redirect("\login")         # Redirect to login page after successful signup



    return render_template('/signup.html')     # Render the signup.html template for GET requests


app.run(host='0.0.0.0', debug=True) # Run the Flask app



   