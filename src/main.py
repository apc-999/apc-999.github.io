import sqlite3
import os
import datetime
import sys
import dateutil.parser
import hashlib
from flask import Flask, render_template, redirect, url_for, g, request, flash, session
from werkzeug.utils import secure_filename

app = Flask(__name__, template_folder='../templates', static_folder='../resources', static_url_path='/resources')
app.secret_key = 'QAsucks'

# Define paths for resources
resources = os.path.join(app.root_path, os.pardir) + "/resources/"
app.config['UPLOAD_FOLDER'] = os.path.join(resources, 'static/images')

# Ensure the upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Database initialisation
db_path = os.path.join(resources, "data.db")

# Function to initialise the database and create necessary tables
def init_db():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # Create data table
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
    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS "users" (
        "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        "username" TEXT NOT NULL UNIQUE,
        "password" TEXT NOT NULL,
        "role" TEXT NOT NULL DEFAULT 'user',
        "profile-img" TEXT NOT NULL DEFAULT 'https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_1280.png'
    )
    ''')
    conn.commit()
    conn.close()

# Call init_db() to ensure the database is ready
init_db()

# Function to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Database connection management
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
    return g.db

# Function to get user information from the database
def get_user_info(user_id, return_info):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    result = cursor.fetchone()
    return result[return_info] if result else None

app.jinja_env.globals.update(get_user_info=get_user_info)

# Function to parse ISO 8601 date strings
def get_datetime_from_iso8601_string(s):
    return dateutil.parser.parse(s)

# Function to generate error messages
def error_message(error=None):
    msg = "ERROR!!!!!!!"
    if error:
        msg += f"\n{error}"
    return msg

# Function to insert data into the database
def insert_data(row):
    with get_db() as db:
        cursor = db.cursor()
        cursor.execute('''
        INSERT INTO data (ShortId, Title, Severity, Status, AssignedGroup, AssigneeIdentity, CreateDate, LastUpdatedDate, "Issue open", "Root cause")
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', row)
        db.commit()

# Function to fetch all data rows from the database
def fetch_data():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM data')
    return cursor.fetchall()

# Function to get database headers
def get_headers():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("PRAGMA table_info(data)")
    columns_info = cursor.fetchall()
    return [column[1] for column in columns_info]

# Function to delete a row based on ShortId
def delete_row(short_id):
    with get_db() as db:
        cursor = db.cursor()
        cursor.execute('DELETE FROM data WHERE ShortId = ?', (short_id,))
        db.commit()
    print(f"Row with ShortId {short_id} has been deleted.")

# Function to update a row based on ShortId
def update_row(short_id, column, new_value):
    with get_db() as db:
        cursor = db.cursor()
        cursor.execute(f'UPDATE data SET "{column}" = ? WHERE ShortId = ?', (new_value, short_id))
        db.commit()
    print(f"Ticket ShortId {short_id} has been updated.")

# Function to get the current datetime in ISO format
def current_datetime():
    return datetime.datetime.utcnow().isoformat() + "Z"

# View all issues
@app.route('/show_issues')
def show_issues():
    error = request.args.get('error')
    all_rows = fetch_data()
    headers = get_headers()
    if not all_rows:
        return "There are no issues currently, please add some."
    return render_template('show_issues.html', error=error, headers=headers, issues=all_rows)

# Add an issue
@app.route('/add_issue', methods=['GET', 'POST'])
def add_issue():
    error = request.args.get('error')
    if 'user_id' not in session:
        return redirect(url_for('show_issues'))
    
    if request.method == 'POST':
        rowtowrite = []
        headers = get_headers()
        
        for header in headers:
            value = request.form.get(header)
            if header in ('CreateDate', 'LastUpdatedDate'):
                # Handle date fields
                if header == "LastUpdatedDate":
                    value = current_datetime()
                elif not value:
                    error = error_message(f'{header} is required.')
                    break
                try:
                    value = get_datetime_from_iso8601_string(value).replace(tzinfo=None).isoformat() + "Z"
                except Exception:
                    error = error_message("Please enter a valid date in ISO8601 format.")
                    break
                rowtowrite.append(value)
                
            elif header == 'Severity':
                # Validate severity
                try:
                    value = float(value)
                    if 1 <= value <= 5:
                        value = int(value) if value != 2.5 else value
                    else:
                        raise ValueError
                except Exception:
                    error = error_message("Severity must be a SEV number between 1-5")
                    break
                rowtowrite.append(value)
                
            elif header == 'Issue open':
                # Handle boolean values
                rowtowrite.append(str(value == 'on').upper())
                
            elif header == 'Status':
                # Validate status
                valid_statuses = ["Assigned", "Researching", "Work in Progress", "Resolved"]
                if value not in valid_statuses:
                    error = error_message(f'Status must be one of {valid_statuses}')
                    break
                rowtowrite.append(value)

            elif header == 'Root cause':
                # Ensure root cause is provided if issue is open
                if not value and str(rowtowrite[-1]).upper() == "FALSE":
                    error = error_message('Root Cause is required if the issue is open.')
                    break
                rowtowrite.append(value)
            else:
                if not value:
                    error = error_message(f'{header} is required.')
                    break
                rowtowrite.append(value)

        if error:
            return render_template('add_issue.html', error=error)
        else:
            insert_data(rowtowrite)
            return redirect(url_for('show_issues'))
    else:
        return render_template('add_issue.html')

# Deleting issues
@app.route('/delete_issue', methods=['GET', 'POST'])
def delete_issue():
    error = request.args.get('error')
    if 'user_id' not in session:
        return redirect(url_for('show_issues'))
    elif get_user_info(session['user_id'], 3) != "admin":
        return redirect(url_for('show_issues', error=error_message("Must be an admin to access that page")))
    
    if request.method == 'POST':
        ticket_id = request.form.get('ticket_id')
        if ticket_id:
            delete_row(ticket_id)
            return redirect(url_for('delete_issue'))

    all_rows = fetch_data()
    headers = get_headers()
    return render_template('delete_issue.html', all_rows=all_rows, headers=headers, error=error)

# Resolve an issue
@app.route('/resolve_issue', methods=['GET', 'POST'])
def resolve_issue():
    if 'user_id' not in session:
        return redirect(url_for('show_issues'))
    error=request.args.get('error')
    all_rows = fetch_data()
    headers = get_headers()

    unresolved_issues = [row for row in all_rows if row[8] == "TRUE"]
    current_root_cause = None

    if request.method == 'POST':
        ticket_id = request.form.get('ticket_id')
        root_cause = request.form.get('root_cause', '').strip()
    

        for row in unresolved_issues:
            if row[0] == ticket_id:
                current_root_cause = row['Root cause'] 
        if not current_root_cause and not root_cause:
            return render_template('resolve_issue.html', 
                                   unresolved_issues=unresolved_issues, 
                                   headers=headers, 
                                   error="Root cause is required to resolve this issue.",
                                   current_root_cause=current_root_cause)
        update_row(ticket_id, 'Issue open', "FALSE")
        update_row(ticket_id, "LastUpdatedDate", current_datetime())
        if root_cause: 
            update_row(ticket_id, 'Root cause', root_cause)

        return redirect(url_for('resolve_issue'))
    if not unresolved_issues:
        print("There are no issues to resolve, please add some.")
        error=error_message("No issues to resolve.")

    return render_template('resolve_issue.html', error=error,unresolved_issues=unresolved_issues, all_rows=all_rows, headers=headers, current_root_cause=current_root_cause)

# Updating issues
@app.route('/update_issue', methods=['GET', 'POST'])
def update_issue():
    if 'user_id' not in session:
        return redirect(url_for('show_issues'))
    elif get_user_info(session['user_id'],3) != "admin":
        return redirect(url_for('show_issues',error=error_message("Must be an admin to access that page")))
    
    db = get_db()
    cursor = db.cursor()
    ticket_id = request.args.get('ticket_id')
    if not ticket_id:
        all_rows = fetch_data()
        headers = get_headers()

        if not all_rows:
            return render_template('show_issues.html', error="There are no issues to update, maybe add some.")

        return render_template('select_issue.html', issues=all_rows, headers=headers)
    
    if request.method == 'POST':
        updated_data = {}
        headers = get_headers()
        
        # Handle Issue open checkbox separately
        issue_open = 'TRUE' if request.form.get('Issue open') == 'on' else 'FALSE'
        update_row(ticket_id, 'Issue open', issue_open)
        
        # Update LastUpdatedDate
        update_row(ticket_id, 'LastUpdatedDate', current_datetime())
        
        # Process other fields
        for header in headers:
            if header != 'Issue open' and header != 'LastUpdatedDate':
                value = request.form.get(header)
                if value and value.strip():
                    update_row(ticket_id, header, value)
        
        return redirect(url_for('show_issues')) 

    else:
        query = "SELECT * FROM data WHERE ShortId = ?"
        cursor.execute(query, (ticket_id,))
        issue = cursor.fetchone()

        if not issue:
            return "Issue not found", 404
        
        headers = get_headers()
        
        return render_template('update_issue.html', issue=issue, headers=headers)

# Search for [an] issue(s)
@app.route('/find_issue', methods=['GET', 'POST'])
def find_issue():
    if 'user_id' not in session:
        return redirect(url_for('show_issues'))
    db = get_db()
    cursor = db.cursor()
    headers = get_headers()  
    matching_rows = []

    if request.method == 'POST':
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

# Register an account
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error=request.args.get('error')
    if 'user_id' in session:
        return redirect(url_for('menu'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
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

# Log in to an account
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

# Change password in a rare case that the password was reset
@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    if request.method == 'POST':
        new_password = hash_password(request.form['new_password'])

        db = get_db()
        cursor = db.cursor()
        cursor.execute('UPDATE users SET password = ? WHERE id = ?', 
                       (new_password, user_id))
        db.commit()
        db.close()

        return redirect(url_for('menu'))

    return render_template('change_password.html')

# Admin dashboard for user management
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
        # Handle adding a new user
        if 'add_user' in request.form:
            new_username = request.form.get('new_username')
            new_password = request.form.get('new_password')
            new_role = request.form.get('new_role')
            new_profile_image = request.files.get('new_profile_image')
            
            if not new_username or not new_password:
                error = error_message("Username and password are required")
            else:
                try:
                    hashed_password = hash_password(new_password)
                    
                    # Handle profile image if provided
                    profile_img_path = "https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_1280.png"
                    if new_profile_image and new_profile_image.filename:
                        filename = secure_filename(new_profile_image.filename)
                        full_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        new_profile_image.save(full_path)
                        # Use proper URL for static files
                        profile_img_path = f"/resources/static/images/{filename}"
                    
                    cursor.execute("INSERT INTO users (username, password, role, \"profile-img\") VALUES (?, ?, ?, ?)", 
                                  (new_username, hashed_password, new_role, profile_img_path))
                    db.commit()
                    error = "User added successfully"
                except sqlite3.IntegrityError:
                    error = error_message("Username already exists")
        else:
            user_id = request.form.get('user_id')
            username = request.form.get('username')
            role = request.form.get('role')
            profile_image=request.files.get('profile_image')
            
            # Handle delete user action
            if 'delete_user' in request.form:
                # Prevent deleting the current user
                if int(user_id) == session['user_id']:
                    error = error_message("You cannot delete your own account")
                else:
                    cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
                    error = "User deleted successfully"
            elif 'reset_password' in request.form:
                cursor.execute('UPDATE users SET password = ? WHERE id = ?', ('default_password', user_id))
            elif 'reset_image' in request.form:
                cursor.execute('UPDATE users SET "profile-img" = "https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_1280.png" WHERE id = ?', (user_id,))
            else:
                if profile_image and profile_image.filename:
                    filename = secure_filename(profile_image.filename)
                    full_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    profile_image.save(full_path)
                    # Use proper URL for static files
                    profile_img_path = f"/resources/static/images/{filename}"
                    cursor.execute('UPDATE users SET username = ?, role = ?, "profile-img" = ? WHERE id = ?',
                                  (username, role, profile_img_path, user_id))
                else:
                    cursor.execute('UPDATE users SET username = ?, role = ? WHERE id = ?',
                                  (username, role, user_id))

        db.commit()
        db.close()
        return redirect(url_for('admin', error=error or "Success"))

    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()
    
    return render_template('admin.html', users=users, error=error)

# Main menu
@app.route('/')
def menu():
    if 'user_id' not in session:
        return redirect(url_for('show_issues'))
    return render_template('menu.html', role=get_user_info(session.get('user_id'), 3))

# Logout of an account
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))


# Not called by PythonAnywhere
if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)