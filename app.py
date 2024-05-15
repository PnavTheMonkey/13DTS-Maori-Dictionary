from flask import Flask, render_template, redirect, request, session  #imports the neccesary modules from Flask
import sqlite3
from sqlite3 import Error
from flask_bcrypt import Bcrypt   #import bcrypt module


DATABASE ='C:/Users/Kartik/OneDrive/13DTS/13DTS-Maori-Dictionary/database.db'   # Define the path to the SQLite database file

app = Flask(__name__)    # Create a Flask application instance
bcrypt = Bcrypt(app)    ## starts Bcrypt with the Flask app
app.secret_key = "uhb*#1e8hp*9x"    # Set a secret key for the Flask application this is the key for hashed password


def create_connection(db_file):       # Function to create a connection to the SQLite database
    try:
        connection = sqlite3.connect(db_file)       # Attempt connection to the SQLite database
        return connection
    except Error as e:
        print(e)           # Print an error message if connection fails
    return None

def is_logged_in(): # Function to check if user is logged in
    if session.get("email") is None:
        print("not logged in ")         # P mrint message if the person is not logged in
        return False
    else:
        print("logged in!")         # Print message if user is logged in
        return True

def is_logged_in_as_teacher():
    if session.get("email") is None:
        print("not logged in as teacher")
        return False
    else:
        email = session.get("email")
        con = create_connection(DATABASE)
        cur = con.cursor()
        cur.execute("SELECT teacher FROM account_table WHERE email=?", (email,))
        user_data = cur.fetchone()
        con.close()
        if user_data and user_data[0]:  # Check if the user is a teacher
            print("logged in as teacher")
            return True
        else:
            print("not logged in as teacher")
            return False

@app.route('/')
def render_homepage():     # Render the home.html template
    return render_template("home.html" , logged_in=is_logged_in())       # This print statement will not

    print("home")  # executed as it comes after the return statement

@app.route('/login', methods=['POST', 'GET'])
def render_login():
    if is_logged_in():      # Check if user is already logged in.
        return redirect('/dictionary/1')
    print("Logging in")
    if request.method == "POST":         # gets email and password from the form
        email = request.form['email'].strip().lower()
        password = request.form['password'].strip()

        query = """SELECT id, fname, password FROM account_table WHERE email = ?"""       # Query to fetch user data from the database
        con = create_connection(DATABASE)         # Create a connection to the database
        cur = con.cursor()
        cur.execute(query, (email, ))
        user_data = cur.fetchone()         # Fetch user data
        con.close()

        try:
            user_id = user_data[0]             # Extract user_id, first_name, and db_password from user_data
            first_name = user_data[1]
            db_password = user_data[2]
            print(f'DB password = {db_password}')
        except IndexError:
            return redirect("/login?error=Invalid+username+or+password")        # Redirect to login page with an error message if user does not exist
        if not bcrypt.check_password_hash(db_password, password):         # Check if the provided password matches the hashed password stored in the database
            return redirect(request.referrer + '?error=Email+invalid+or+password+incorrect')        # Redirect to the previous page with an error message if password is incorrect

        # Create session variables
        session['email'] = email
        session['userid'] = user_id
        session['firstname'] = first_name
        print(session)
        return redirect('/')   #returns them home once logged in
    return render_template("login.html", logged_in=is_logged_in())      # Render the login page for GET requests

@app.route('/signup', methods=['POST', 'GET'])
def render_signup():
    if is_logged_in():      # Check if user is already logged in.
        return redirect('/dictionary/1')
    if request.method == 'POST':
        print(request.form)

        fname = request.form.get('fname').title().strip()   # Extract form data
        lname = request.form.get('lname').title().strip()
        email = request.form.get('email').lower().strip()
        password = request.form.get('password')
        password2 = request.form.get('password2')
        teacher = request.form.get('role')

        if password != password2:            # Check if passwords match
            return redirect("\signup?error='Passwords+do+not+match")

        if len(password) < 8:         # Check if password is at least 8 characters long
            return redirect("\signup?error='Password+must+be+at+least+8+characters")



        hashed_password = bcrypt.generate_password_hash(password)         # Hash the password
        con = create_connection(DATABASE)        # Open a connection to the database
        query = "INSERT INTO account_table (fname, lname, email, password, teacher) VALUES (?,?,?,?,?)"
        cur = con.cursor()
        print()
        try:
            cur.execute(query, (fname, lname, email, hashed_password, teacher))
        except sqlite3.IntegrityError:
            con.close()
            return redirect("\signup?error='Email is already in use.")

        con.commit()         # Commit changes and close connection
        con.close()

        return redirect("\login")         # Redirect to login page after successful signup


    return render_template('/signup.html' , logged_in=is_logged_in())     # Render the signup.html template for GET requests

@app.route('/dictionary/<cat_id>')
def render_dictionary_page(cat_id):
    search_term = request.args.get('search', '')  # Get the search term from the query parameter
    con = create_connection(DATABASE)
    query = "SELECT * FROM word_table WHERE cat_id=?"

    if search_term:
        query += " AND (english_word LIKE ? OR te_reo_word LIKE ?)"  # Update the query to include search conditions
        search_param = f"%{search_term}%"    # Define search parameters
        cur = con.cursor()
        cur.execute(query, (cat_id, search_param, search_param))    # Execute the query with search parameters
    else:
        cur = con.cursor()
        cur.execute(query, (cat_id,))

    word_table = cur.fetchall()

    query = "SELECT id, name FROM catergories_list"
    cur = con.cursor()
    cur.execute(query)
    catergory_list = cur.fetchall()
    con.close()
    print(word_table, catergory_list)

    return render_template('dictionary.html', words=word_table, catergories=catergory_list, search_term=search_term, cat_id=cat_id , logged_in=is_logged_in())

@app.route('/logout')
def logout():
    print(list(session.keys()))
    [session.pop(key) for key in list(session.keys())]   #removes the stuff from session
    print(list(session.keys()))
    return redirect('/?message=Later+cuz!')


@app.route('/admin')
def render_admin():
    if not is_logged_in():  # Check if user is logged in
        return redirect('/login?error=Need+to+be+logged+in')
    elif not is_logged_in_as_teacher():  # Check if user is logged in as a teacher
        return redirect('/?error=Only+teachers+can+access+the+admin+page')

    return render_template('admin.html', logged_in=is_logged_in())



@app.route('/add_word', methods=['POST'])
def add_word():
    if not is_logged_in():
        return redirect("/login")

    english_word = request.form['english_word']
    te_reo_word = request.form['te_reo_word']
    cat_id = request.form['category']

    con = create_connection(DATABASE)
    cur = con.cursor()
    cur.execute("INSERT INTO word_table (english_word, te_reo_word, cat_id) VALUES (?, ?, ?)", (english_word, te_reo_word, cat_id))
    con.commit()
    con.close()

    return redirect("/admin")


@app.route('/words_info/<word_id>')
def render_words_info(word_id):
    con = create_connection(DATABASE)
    query = "SELECT * " \
            "FROM word_table" \
            "WHERE words_id=?"

    cur = con.cursor()
    cur.execute(query, (word_id, ))
    all_word_info = cur.fetchall
    con.close
    print(all_word_info)


@app.route('/delete_word', methods=['POST'])
def delete_word():
    if not is_logged_in():
        return redirect("/login")

    english_word = request.form['english_word']
    te_reo_word = request.form['te_reo_word']

    con = create_connection(DATABASE)
    cur = con.cursor()
    cur.execute("DELETE FROM word_table WHERE english_word = ? AND te_reo_word = ?", (english_word, te_reo_word))
    con.commit()

@app.route('/add_word', methods=['POST'])
def add_word_route():
    if not is_logged_in():
        return redirect("/login")

    english_word = request.form['english_word']
    te_reo_word = request.form['te_reo_word']
    cat_id = request.form['category']

    con = create_connection(DATABASE)
    cur = con.cursor()
    cur.execute("INSERT INTO word_table (english_word, te_reo_word, cat_id) VALUES (?, ?, ?)", (english_word, te_reo_word, cat_id))
    con.commit()
    con.close()

    return redirect("/admin")

if __name__ == '__main__':
        app.run(debug=True)



app.run(host='0.0.0.0', debug=True) # Run the Flask app



