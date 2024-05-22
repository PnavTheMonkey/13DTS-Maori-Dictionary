from flask import Flask, render_template, redirect, request, session  # Import necessary modules from Flask
import sqlite3  # Import SQLite3 for database management
from sqlite3 import Error  # Import the Error class for handling database errors
from flask_bcrypt import Bcrypt  # Import Bcrypt module for password hashing

DATABASE = 'C:/Users/Kartik/OneDrive/13DTS/13DTS-Maori-Dictionary/database.db'  # Define the path to the SQLite database file

app = Flask(__name__)  # Create a Flask application instance
bcrypt = Bcrypt(app)  # Initialize Bcrypt with the Flask app
app.secret_key = "uhb*#1e8hp*9x"  # Set a secret key for the Flask application for session management

def create_connection(db_file):  # Function to create a connection to the SQLite database
    try:
        connection = sqlite3.connect(db_file)  # Attempt connection to the SQLite database
        return connection  # Return the connection object if successful
    except Error as e:  # Handle connection errors
        print(e)  # Print an error message if connection fails
    return None  # Return None if connection fails

def is_logged_in():  # Function to check if user is logged in
    if session.get("email") is None:  # Check if "email" is not in session
        print("not logged in")  # Print message if user is not logged in
        return False  # Return False if user is not logged in
    else:  # If "email" is in session
        print("logged in!")  # Print message if user is logged in
        return True  # Return True if user is logged in

def is_logged_in_as_teacher():  # Function to check if user is logged in as a teacher
    if session.get("email") is None:  # Check if "email" is not in session
        return False  # Return False if user is not logged in
    else:  # If "email" is in session
        email = session.get("email")  # Get email from session
        con = create_connection(DATABASE)  # Create a connection to the database
        cur = con.cursor()  # Create a cursor object
        cur.execute("SELECT teacher FROM account_table WHERE email=?", (email,))  # Execute query to check if user is a teacher
        user_data = cur.fetchone()  # Fetch one result
        con.close()  # Close the connection
        if user_data and user_data[0]:  # Check if the user is a teacher
            return True  # Return True if user is a teacher
        else:  # If not a teacher
            return False  # Return False if user is not a teacher

@app.route('/')  # Route for the homepage
def render_homepage():  # Function to render the homepage
    return render_template("home.html", logged_in=is_logged_in())  # Render home.html with logged_in status

@app.route('/login', methods=['POST', 'GET'])  # Route for the login page
def render_login():  # Function to render the login page
    if is_logged_in():  # Check if user is already logged in
        return redirect('/dictionary/1')  # Redirect to dictionary page if logged in

    if request.method == "POST":  # Check if request method is POST
        email = request.form['email'].strip().lower()  # Get and clean email from form
        password = request.form['password'].strip()  # Get and clean password from form

        query = """SELECT account_id, fname, password FROM account_table WHERE email = ?"""  # Define query
        con = create_connection(DATABASE)  # Create a connection to the database
        cur = con.cursor()  # Create a cursor object
        cur.execute(query, (email,))  # Execute the query
        user_data = cur.fetchone()  # Fetch one result
        con.close()  # Close the connection

        if user_data is None:  # Check if user data is None
            return redirect("/login?error=Invalid+username+or+password")  # Redirect with error if user not found

        user_id, first_name, db_password = user_data  # Unpack user data

        if not bcrypt.check_password_hash(db_password, password):  # Check if password is incorrect
            return redirect(request.referrer + '?error=Email+invalid+or+password+incorrect')  # Redirect with error

        session['email'] = email  # Set email in session
        session['userid'] = user_id  # Set user ID in session
        session['firstname'] = first_name  # Set first name in session

        return redirect('/')  # Redirect to homepage once logged in

    return render_template("login.html", logged_in=is_logged_in())  # Render login.html for GET requests

@app.route('/signup', methods=['POST', 'GET'])  # Route for the signup page
def render_signup():  # Function to render the signup page
    if is_logged_in():  # Check if user is already logged in
        return redirect('/dictionary/1')  # Redirect to dictionary page if logged in
    if request.method == 'POST':  # Check if request method is POST
        print(request.form)  # Print form data for debugging

        fname = request.form.get('fname').title().strip()  # Extract and clean form data
        lname = request.form.get('lname').title().strip()
        email = request.form.get('email').lower().strip()
        password = request.form.get('password')
        password2 = request.form.get('password2')
        teacher = request.form.get('role')

        if password != password2:  # Check if passwords match
            return redirect("\signup?error='Passwords+do+not+match")  # Redirect with error if passwords do not match

        if len(password) < 8:  # Check if password is at least 8 characters long
            return redirect("\signup?error='Password+must+be+at+least+8+characters")  # Redirect with error if password too short

        hashed_password = bcrypt.generate_password_hash(password)  # Hash the password
        con = create_connection(DATABASE)  # Create a connection to the database
        query = "INSERT INTO account_table (fname, lname, email, password, teacher) VALUES (?,?,?,?,?)"  # Define query
        cur = con.cursor()  # Create a cursor object
        print()  # Print empty line for debugging

        try:  # Try to execute the query
            cur.execute(query, (fname, lname, email, hashed_password, teacher))  # Execute query
        except sqlite3.IntegrityError:  # Handle integrity error
            con.close()  # Close the connection
            return redirect("\signup?error='Email is already in use.")  # Redirect with error if email is already in use

        con.commit()  # Commit changes
        con.close()  # Close the connection

        return redirect("\login")  # Redirect to login page after successful signup

    return render_template('/signup.html', logged_in=is_logged_in())  # Render signup.html for GET requests

@app.route('/dictionary/<cat_id>')  # Route for the dictionary page
def render_dictionary_page(cat_id):  # Function to render the dictionary page
    search_term = request.args.get('search', '')  # Get the search term from query
    con = create_connection(DATABASE)  # Create a connection to the database
    query = """
      SELECT *  FROM word_table
      INNER JOIN categories_list ON word_table.cat_id = categories_list.category_id 
      WHERE word_table.cat_id=?
      """  # Define query and the Inner join between the tables

    if search_term:  # Check if there is a search term
        query += " AND (english_word LIKE ? OR te_reo_word LIKE ?)"  # Update the query to include search conditions
        search_param = f"%{search_term}%"  # Define search
        cur = con.cursor()  # Create a cursor object
        cur.execute(query, (cat_id, search_param, search_param))  # Execute the query with search
    else:  # If no search term
        cur = con.cursor()  # Create a cursor object
        cur.execute(query, (cat_id,))  # Execute the query

    word_table = cur.fetchall()  # Fetch all results

    query = "SELECT category_id, name FROM categories_list"  # Define query to get categories
    cur = con.cursor()  # Create a cursor object
    cur.execute(query)  # Execute the query
    catergory_list = cur.fetchall()  # Fetch all results
    con.close()  # Close the connection
    print(word_table, catergory_list)  # Print results for debugging

    return render_template('dictionary.html', words=word_table, catergories=catergory_list, search_term=search_term, cat_id=cat_id, logged_in=is_logged_in())  # Render dictionary.html

@app.route('/logout')  # Route for logout
def logout():  # Function to handle logout
    print(list(session.keys()))  # Print current session keys for debugging
    [session.pop(key) for key in list(session.keys())]  # Remove all session keys
    print(list(session.keys()))  # Print session keys after logout for debugging
    return redirect('/?message=Later+cuz!')  # Redirect to homepage with message

@app.route('/admin')  # Route for the admin page
def render_admin():  # Function to render the admin page
    if not is_logged_in():  # Check if user is logged in
        return redirect('/login?error=Need+to+be+logged+in')  # Redirect to login with error if not logged in
    elif not is_logged_in_as_teacher():  # Check if user is logged in as a teacher
        return redirect('/?error=Only+teachers+can+access+the+admin+page')  # Redirect to homepage with error if not a teacher

    con = create_connection(DATABASE)  # Create a connection to the database
    query = "SELECT * FROM categories_list"  # Define query to get categories
    cur = con.cursor()  # Create a cursor object
    cur.execute(query)  # Execute the query
    categories_list = cur.fetchall()  # Fetch all results
    con.close()  # Close the connection
    return render_template('admin.html', logged_in=is_logged_in(), categories=categories_list)  # Render admin.html

@app.route('/words_info/<word_id>')  # Route for word info page
def render_words_info(word_id):  # Function to render word info page
    if not is_logged_in():  # Check if user is logged in
        return redirect('/login?error=Need+to+be+logged+in')  # Redirect to login with error if not logged in

    con = create_connection(DATABASE)  # Create a connection to the database
    query = "SELECT * FROM word_table WHERE word_id=?"  # Define query to get word info

    cur = con.cursor()  # Create a cursor object
    cur.execute(query, (word_id,))  # Execute the query
    all_word_info = cur.fetchall()  # Fetch all results
    con.close()  # Close the connection
    print(all_word_info)  # Print word info for debugging
    return render_template("words_info.html", all_word_info=all_word_info)  # Render words_info.html

@app.route('/delete_word/<word_id>', methods=['GET', 'POST'])  # Route for delete word confirmation
def delete_word(word_id):  # Function to handle delete word
    if not is_logged_in():  # Check if user is logged in
        return redirect('/login?error=Need+to+be+logged+in')  # Redirect to login with error if not logged in
    elif not is_logged_in_as_teacher():  # Check if user is logged in as a teacher
        return redirect('/?error=Only+teachers+can+access+the+admin+page')  # Redirect to homepage with error if not a teacher
    print('a')  # Print for debugging
    print(word_id)  # Print word ID for debugging

    con = create_connection(DATABASE)  # Create a connection to the database
    cur = con.cursor()  # Create a cursor object
    query = "SELECT english_word FROM word_table WHERE word_id = ?"  # Define query to get word info
    cur.execute(query, (word_id,))  # Execute the query
    english_word = cur.fetchone()  # Fetch one result
    con.close()  # Close the connection
    print(english_word)  # Print word info for debugging
    return render_template('delete_word_confirmed.html', name=english_word, id=word_id)  # Render delete_word_confirmed.html

@app.route('/delete_word_confirmed/<word_id>')  # Route for confirming word deletion
def delete_word_confirmed(word_id):  # Function to confirm word deletion
    if not is_logged_in():  # Check if user is logged in
        return redirect('/?message=Need+to+be+logged+in')  # Redirect to homepage with message if not logged in

    con = create_connection(DATABASE)  # Create a connection to the database
    cur = con.cursor()  # Create a cursor object
    cur.execute("DELETE FROM word_table WHERE word_id = ?", (word_id,))  # Execute delete query
    con.commit()  # Commit changes
    con.close()  # Close the connection

    return redirect("/admin")  # Redirect to admin page

@app.route('/add_word', methods=['GET', 'POST'])  # Route for adding a word
def add_word_route():  # Function to handle adding a word
    if not is_logged_in():  # Check if user is logged in
        return redirect("/login")  # Redirect to login if not logged in

    if request.method == 'POST':  # Check if request method is POST
        english_word = request.form['english_word']  # Get form data
        te_reo_word = request.form['te_reo_word']
        level = request.form['level']
        description = request.form['description']
        cat_id = request.form['cat_id']

        con = create_connection(DATABASE)  # Create a connection to the database
        cur = con.cursor()  # Create a cursor object
        cur.execute("""
            INSERT INTO word_table (english_word, te_reo_word, level, description, cat_id)
            VALUES (?, ?, ?, ?, ?)
        """, (english_word, te_reo_word, level, description, cat_id))  # Execute insert query
        con.commit()  # Commit changes
        con.close()  # Close the connection

        return redirect("/admin")  # Redirect to admin page

    con = create_connection(DATABASE)  # Create a connection to the database
    cur = con.cursor()  # Create a cursor object
    cur.execute("SELECT word_id, name FROM categories_list")  # Execute query to get categories
    categories = cur.fetchall()  # Fetch all results
    con.close()  # Close the connection

    return render_template('admin.html', categories=categories, logged_in=is_logged_in())  # Render admin.html

@app.route('/category_add', methods=['POST'])  # Route for adding a category
def category_add():  # Function to handle adding a category
    if not is_logged_in():  # Check if user is logged in
        return redirect('/?message=Need+to+be+logged+in')  # Redirect to homepage with message if not logged in
    if request.method == 'POST':  # Check if request method is POST
        print(request.form)  # Print form data for debugging
        cat_name = request.form.get('name').strip()  # Get and clean category name
        print(cat_name)  # Print category name for debugging
        con = create_connection(DATABASE)  # Create a connection to the database
        query = "INSERT INTO categories_list ('name') VALUES (?)"  # Define insert query
        cur = con.cursor()  # Create a cursor object
        cur.execute(query, (cat_name,))  # Execute query
        con.commit()  # Commit changes
        con.close()  # Close the connection
        return redirect('/admin')  # Redirect to admin page

@app.route('/category_delete', methods=['POST', 'GET'])  # Route for deleting a category
def render_category_delete():  # Function to handle category deletion
    if not is_logged_in():  # Check if user is logged in
        return redirect('/dictionary/1')  # Redirect to dictionary page if not logged in

    if request.method == 'POST':  # Check if request method is POST
        cat_id = request.form.get('cat_id')  # Get category ID from form

        if not cat_id:  # Check if category ID is not provided
            return redirect('/admin?error=Category+not+selected')  # Redirect with error if not selected

        con = create_connection(DATABASE)  # Create a connection to the database
        cur = con.cursor()  # Create a cursor object
        cur.execute("SELECT name FROM categories_list WHERE category_id = ?", (cat_id,))  # Execute query to get category info
        category = cur.fetchone()  # Fetch one result
        con.close()  # Close the connection

        if not category:  # Check if category is not found
            return redirect('/admin?error=Category+not+found')  # Redirect with error if not found

        cat_name = category[0]  # Get category name
        return render_template("delete_word_confirmed.html", id=cat_id, name=cat_name, type="category")  # Render confirmation page

    con = create_connection(DATABASE)  # Create a connection to the database
    cur = con.cursor()  # Create a cursor object
    cur.execute("SELECT category_id, name FROM categories_list")  # Execute query to get categories
    categories = cur.fetchall()  # Fetch all results
    con.close()  # Close the connection

    return render_template('delete_category.html', categories=categories, logged_in=is_logged_in())  # Render delete_category.html

@app.route('/category_confirm_delete/<int:cat_id>', methods=['POST'])  # Route to confirm category deletion
def category_confirm_delete(cat_id):  # Function to confirm category deletion
    if not is_logged_in():  # Check if user is logged in
        return redirect('/?message=Need+to+be+logged+in')  # Redirect to homepage with message if not logged in

    con = create_connection(DATABASE)  # Create a connection to the database
    cur = con.cursor()  # Create a cursor object
    cur.execute("DELETE FROM categories_list WHERE category_id = ?", (cat_id,))  # Execute delete query
    con.commit()  # Commit changes
    con.close()  # Close the connection

    return redirect("/admin")  # Redirect to admin page

if __name__ == '__main__':  # Check if the script is executed directly
    app.run(debug=True)  # Run the Flask app in debug mode
app.run(host='0.0.0.0', debug=True)  # Run the Flask app accessible from any network interface in debug mode
