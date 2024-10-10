import sqlite3
import os
import datetime
import sys
import dateutil.parser
from tkinter import messagebox as mb
from flask import Flask, render_template, redirect, url_for, g, request, render_template_string, session, flash
from tkinter import Tk, PhotoImage
from werkzeug.utils import secure_filename
import hashlib
app = Flask(__name__, template_folder='../templates', static_folder='../resources')
app.secret_key = 'QAsucks'

resources=os.path.join(app.root_path, os.pardir)+"/resources/"
app.config['UPLOAD_FOLDER'] = resources+'static/images'

if not os.path.exists(app.config['UPLOAD_FOLDER'] ):
    os.makedirs(app.config['UPLOAD_FOLDER'])
print(resources)
db_path = resources+"data.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS data (
    ShortId TEXT,
    Title TEXT,
    Severity TEXT,
    Status TEXT,
    AssignedGroup TEXT,
    AssigneeIdentity TEXT,
    CreateDate TEXT,
    LastUpdatedDate TEXT,
    "Issue open" BOOLEAN,
    "Root cause" TEXT
)
''')
cursor.execute('''CREATE TABLE IF NOT EXISTS "users" (
	"id"	INTEGER NOT NULL,
	"username"	TEXT NOT NULL UNIQUE,
	"password"	TEXT NOT NULL,
	"role"	TEXT NOT NULL DEFAULT 'user',
	"profile-img"	TEXT NOT NULL DEFAULT 'https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_1280.png',
	PRIMARY KEY("id" AUTOINCREMENT)
)''')
conn.commit()
conn.close()

# Password hashing
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
    return g.db
def get_user_info(user_id,return_info):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    result = cursor.fetchone()
    return result[return_info] if result else None
app.jinja_env.globals.update(get_user_info=get_user_info)
def getDateTimeFromISO8601String(s):
    d = dateutil.parser.parse(s)
    return d
def error_message(error=None):
    msg = "ERROR!!!!!!!"
    if error:
        msg += "\n" + error
    return msg
def insert_data(row):
    with get_db() as db:
        print(row)
        cursor = db.cursor()
        cursor.execute('''
        INSERT INTO data (ShortId, Title, Severity, Status, AssignedGroup, AssigneeIdentity, CreateDate, LastUpdatedDate, "Issue open", "Root cause")
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', row)
        db.commit()
def fetch_data():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM data')
    return cursor.fetchall()
def get_headers():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("PRAGMA table_info(data)")
    columns_info = cursor.fetchall()
    headers = [column[1] for column in columns_info]
    return headers
def delete_row(short_id):
    with get_db() as db:
        cursor = db.cursor()
        cursor.execute('DELETE FROM data WHERE ShortId = ?', (short_id,))
        db.commit()
    print(f"Row with ShortId {short_id} has been deleted.")
def update_row(short_id, column, new_value):
    print(short_id, column, new_value)
    with get_db() as db:
        cursor = db.cursor()
        query = f'''UPDATE data SET "{column}" = ? WHERE ShortId = ?'''
        print(query)
        cursor.execute(query, (new_value, short_id))
        db.commit()
    print(f"Ticket ShortId {short_id} has been updated.")
def current_datetime():
    return datetime.datetime.utcnow().isoformat()+"Z"
@app.route('/show_issues')
def show_issues():
    error=request.args.get('error')
    all_rows = fetch_data()
    headers = get_headers()
    if not all_rows:
        return "There are no issues currently, please add some."

    return render_template('show_issues.html', error=error, headers=headers, issues=all_rows)
@app.route('/add_issue', methods=['GET', 'POST'])
def add_issue():
    error=request.args.get('error')
    if 'user_id' not in session:
        return redirect(url_for('show_issues'))
    if request.method == 'POST':
        rowtowrite = []
        headers = get_headers()
        
        # Process form data
        for header in headers:
            value=request.form.get(header)
            if header == 'CreateDate' or header == 'LastUpdatedDate':
                if header=="LastUpdatedDate":
                    value=current_datetime()
                elif not value:
                    print("there's an error at Date")
                    error = error_message(error=f'{header} is required.')
                    break
                try:
                    value = getDateTimeFromISO8601String(value).replace(tzinfo=None).isoformat()+"Z"
                except:
                    print("there's an error at ISO Date")
                    error = error_message(error="Please enter a valid date in ISO8601 format.")
                    break
                rowtowrite.append(value)
                
            elif header == 'Severity':
                try:
                    value = float(value)
                    if 1 <= value <= 5:
                        value = int(value) if value != 2.5 else value
                    else:
                        raise ValueError
                except:
                    print("there's an error at sev")
                    error = error_message(error="Severity must be a SEV number between 1-5")
                    failed=True
                    break
                rowtowrite.append(value)
                
            elif header == 'Issue open':
                print(value)
                issue_open = value == 'on'
                rowtowrite.append(str(issue_open).upper())
                
            elif header == 'Status':
                valid_statuses = ["Assigned", "Researching", "Work in Progress", "Resolved"]
                if value not in valid_statuses:
                    print("there's an error at status")
                    error = error_message(error=f'Status must be one of {valid_statuses}')
                    failed=True
                    break
                rowtowrite.append(value)
            elif header == 'Root cause':
                print(rowtowrite[-1])
                if not value and str(rowtowrite[-1]).upper() == "FALSE":  # Check if the issue is open
                    error = error_message( error=f'Root Cause is required if the issue is open.')
                    break
                rowtowrite.append(value)  # Append even if it's empty
            else:
                print(header,value)
                if not value:
                    print("there's an error at not value")
                    error = error_message(error=f'{header} is required.')
                    break
                rowtowrite.append(value)

        # Insert the new row into the database
        if error:
            print(error)
            return render_template('add_issue.html', error=error)
        else:
            insert_data(rowtowrite)
            return redirect(url_for('show_issues'))
    else:
    # For GET requests, show the form
        return render_template('add_issue.html')
@app.route('/delete_issue', methods=['GET', 'POST'])
def delete_issue():
    error=request.args.get('error')
    if 'user_id' not in session:
        return redirect(url_for('show_issues'))
    elif get_user_info(session['user_id'],3) != "admin":
        return redirect(url_for('show_issues',error=error_message("Must be an admin to access that page")))
    if request.method == 'POST':
        # Get the ticket ID from the form submission
        ticket_id = request.form.get('ticket_id')
        if ticket_id:
            delete_row(ticket_id)  # Call your function to delete the row
            return redirect(url_for('delete_issue'))  # Redirect to the delete page after deletion

    # For GET requests, display all rows
    all_rows = fetch_data()
    headers = get_headers()
    return render_template('delete_issue.html', all_rows=all_rows, headers=headers,error=error)
@app.route('/resolve_issue', methods=['GET', 'POST'])
def resolve_issue():
    if 'user_id' not in session:
        return redirect(url_for('show_issues'))
    error=request.args.get('error')
    all_rows = fetch_data()
    headers = get_headers()

    unresolved_issues = [row for row in all_rows if row[8] == "TRUE"]  # Assuming the status is in column 8
    current_root_cause = None

    if request.method == 'POST':
        # Handle the form submission to resolve an issue
        ticket_id = request.form.get('ticket_id')
        root_cause = request.form.get('root_cause', '').strip()
    

        for row in unresolved_issues:
            if row[0] == ticket_id:  # Adjust based on your ticket identifier
                current_root_cause = row['Root cause']  # Use the actual column 
        print(current_root_cause)
        # If there's no current root cause, require a new one
        if not current_root_cause and not root_cause:
            return render_template('resolve_issue.html', 
                                   unresolved_issues=unresolved_issues, 
                                   headers=headers, 
                                   error="Root cause is required to resolve this issue.",
                                   current_root_cause=current_root_cause)
        print(ticket_id)
        update_row(ticket_id, 'Issue open', "FALSE")
        update_row(ticket_id, "LastUpdatedDate", current_datetime())
        if root_cause: 
            update_row(ticket_id, 'Root cause', root_cause)

        return redirect(url_for('resolve_issue'))  # Redirect to the same page to avoid resubmission

    if not unresolved_issues:
        print("There are no issues to resolve, please add some.")
        error=error_message("No issues to resolve.")

    return render_template('resolve_issue.html', error=error,unresolved_issues=unresolved_issues, all_rows=all_rows, headers=headers, current_root_cause=current_root_cause)

@app.route('/update_issue', methods=['GET', 'POST'])
def update_issue():
    if 'user_id' not in session:
        return redirect(url_for('show_issues'))
    elif get_user_info(session['user_id'],3) != "admin":
        return redirect(url_for('show_issues',error=error_message("Must be an admin to access that page")))
    
    db = get_db()
    cursor = db.cursor()
    ticket_id = request.args.get('ticket_id')  # Get the ticket ID from the URL

    if not ticket_id:
        # If no ticket_id is provided, fetch all issues and render the selection page
        all_rows = fetch_data()  # Fetch all rows
        headers = get_headers()

        if not all_rows:
            return render_template('show_issues.html', error="There are no issues to update, maybe add some.")

        return render_template('select_issue.html', issues=all_rows, headers=headers)
    
    if request.method == 'POST':
        # This block handles form submission for updating the issue
        updated_data = {}
        headers = get_headers()
        
        # Collect form data
        for header in headers:
            updated_data[header] = request.form.get(header)
        
        # Update each field in the database where there was a change
        for header, new_value in updated_data.items():
            if new_value and new_value.strip():  # Ensure no empty values
                update_row(ticket_id, header, new_value)
        
        # After updating, redirect to show_issues or confirmation page
        return redirect(url_for('show_issues'))  # or another success page

    else:
        # For a GET request, fetch and display the issue's details in the form
        query = "SELECT * FROM data WHERE ShortId = ?"
        cursor.execute(query, (ticket_id,))
        issue = cursor.fetchone()

        if not issue:
            return "Issue not found", 404  # Handle case where the ticket doesn't exist
        
        headers = get_headers()
        
        # Render the form pre-filled with the issue's current details
        return render_template('update_issue.html', issue=issue, headers=headers)


@app.route('/find_issue', methods=['GET', 'POST'])
def find_issue():
    if 'user_id' not in session:
        return redirect(url_for('show_issues'))
    db = get_db()
    cursor = db.cursor()
    headers = get_headers()  # Assumes you have a function to get column headers
    matching_rows = []  # Initialize empty list to hold results

    if request.method == 'POST':  # When the search form is submitted
        search_term = request.form.get('search_term')
        query = '''SELECT * FROM data 
                   WHERE ShortId LIKE ? OR Title LIKE ? OR Severity LIKE ? 
                   OR Status LIKE ? OR AssignedGroup LIKE ? 
                   OR AssigneeIdentity LIKE ? OR "Root cause" LIKE ?'''
        search_term_wildcard = f"%{search_term}%"
        cursor.execute(query, (search_term_wildcard, search_term_wildcard, 
                               search_term_wildcard, search_term_wildcard, 
                               search_term_wildcard, search_term_wildcard, 
                               search_term_wildcard))
        matching_rows = cursor.fetchall()

    return render_template('find_issue.html', headers=headers, matching_rows=matching_rows)

# Sign-up route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error=request.args.get('error')
    if 'user_id' in session:
        return redirect(url_for('menu'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Hash the password
        hashed_password = hash_password(password)
        
        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
            db.commit()
            db.close()
            flash('Sign-up successful! You can now log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            error=error_message('Username already exists. Please choose a different one.')
    
    return render_template('signup.html',error=error)

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    error=request.args.get('error')
    if 'user_id' in session:
        return redirect(url_for('menu'))
    if request.method == 'POST':
        username = request.form['username']
        password = hash_password(request.form['password'])
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ? AND (password = ? OR password = "default_password")', (username, password))
        user = cursor.fetchone()
        db.close()
        if user:
            if user[2]=="default_password":
                error = "Your password has been reset. Please create a new password."
                session['user_id'] = user[0]
                return redirect(url_for('change_password'))

            session['user_id'] = user[0]
            return redirect(url_for('menu'))
        else:
            error=error_message('Invalid username or password.')
    
    return render_template('login.html',error=error)
@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Ensure only logged-in users can access this

    user_id = session['user_id']

    if request.method == 'POST':
        new_password = hash_password(request.form['new_password'])

        db = get_db()
        cursor = db.cursor()
        cursor.execute('UPDATE users SET password = ? WHERE id = ?', 
                       (new_password, user_id))
        db.commit()
        db.close()

        return redirect(url_for('menu'))  # Redirect to the main menu after changing password

    return render_template('change_password.html')  # Render a template for changing the password

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    error=request.args.get('error')
    if 'user_id' not in session:
        return redirect(url_for('login'))
    elif get_user_info(session['user_id'],3) != "admin":
        return redirect(url_for('show_issues',error=error_message("Must be an admin to access that page")))
    db = get_db()
    cursor = db.cursor()
    
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        username = request.form.get('username')
        role = request.form.get('role')
        profile_image=request.files.get('profile_image')
        if 'reset_password' in request.form:
            cursor.execute('UPDATE users SET password = ? WHERE id = ?', ('default_password', user_id))
        elif 'reset_image' in request.form:
            cursor.execute('UPDATE users SET "profile-img" = "https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_1280.png" WHERE id = ?', (user_id))
        else:
            if profile_image:
                print("yes")
                # Save the profile image and update the path in the database
                filename = secure_filename(profile_image.filename)
                full_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                profile_image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                cursor.execute('UPDATE users SET username = ?, role = ?, "profile-img" = ? WHERE id = ?',
                               (username, role, full_path, user_id))
            else:
                cursor.execute('UPDATE users SET username = ?, role = ? WHERE id = ?',
                               (username, role, user_id))

        db.commit()
        db.close()
        return redirect(url_for('admin', error="Success"))

    # Fetch all users for display
    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()
    
    return render_template('admin.html', users=users, error=error)

@app.route('/')
def menu():
    if 'user_id' not in session:
        return redirect(url_for('show_issues'))
    return render_template('menu.html',role=get_user_info(session.get('user_id'),3))
# Logout route
@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)
    session.pop('user_id', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)


