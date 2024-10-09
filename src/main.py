import sqlite3
import os
import datetime
import sys
import dateutil.parser
from tkinter import messagebox as mb
from flask import Flask, render_template, redirect, url_for, g, request, render_template_string
from tkinter import Tk, PhotoImage
app = Flask(__name__, template_folder='../templates', static_folder='../resources')
resources=os.path.join(app.root_path, os.pardir)+"/resources/"
print(resources)
db_path = resources+"data.db"
if not os.path.isfile(db_path):
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
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
    return g.db
def getDateTimeFromISO8601String(s):
    d = dateutil.parser.parse(s)
    return d
def error_message(error=None):
    msg = "ERROR!!!!!!!"
    if error:
        msg += "\n" + error
    # Inject a small inline script to trigger the error modal
    return render_template_string(f'''
        <script>
            window.onload = function() {{
                showError("{msg}");
            }};
        </script>
    ''')
##    root = Tk()
##    root.withdraw()
##    root.tk.call('wm', 'iconphoto', root._w, PhotoImage(file=f'{resources}error.gif'))
##    msg="ERROR!!!!!!!"
##    if error:
##        msg+="\n"+error
##    mb.showinfo(title='Error', message=msg)
##    root.destroy()
##    try:
##        root.update()
##    except:
##        root=None
##    return
def yes_no(question):
    root = Tk()
    root.withdraw()
    root.tk.call('wm', 'iconphoto', root._w, PhotoImage(file=f'{resources}question.png'))
    msg= mb.askquestion(title='Question, Yes or No?', message=question)
    root.destroy()
    try:
        root.update()
    except:
        root=None
    return msg == "yes"
def confirmation():
    confirm = yes_no("Are You sure?")
    if not confirm:
        main()
    exit()
def insert_data(row):
    db = get_db()
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
    db = get_db()
    cursor = db.cursor()
    cursor.execute('DELETE FROM data WHERE ShortId = ?', (short_id,))
    conn.commit()
    print(f"Row with ShortId {short_id} has been deleted.")
def update_row(short_id, column, new_value):
    db = get_db()
    cursor = db.cursor()
    query = f'''UPDATE data SET "{column}" = ? WHERE ShortId = ?'''
    cursor.execute(query, (new_value, short_id))
    conn.commit()
    print(f"Ticket ShortId {short_id} has been updated.")
def current_datetime():
    return datetime.datetime.utcnow().isoformat()+"Z"
@app.route('/show_issues')
def show_issues():
    all_rows = fetch_data()
    headers = get_headers()
    if not all_rows:
        return "There are no issues currently, please add some."

    return render_template('show_issues.html', headers=headers, issues=all_rows)
##@app.route('/add_issue')
##def add_issue():
##    rowtowrite=[]
##   
##    headers=get_headers()
##    for header in headers:
##        if "Date" in header:
##            if header=="LastUpdatedDate":
##                writer=current_datetime()
##            else:
##                try:
##                    date=input(f'{header}:\t')
##                    date=current_datetime() if date=="now" else date
##                    writer=getDateTimeFromISO8601String(date).replace(tzinfo=None).isoformat()+"Z"
##                except:
##                    error_message(error="That is not a valid date, Please use the ISO8601 UTC format")
##                    main()
##                    exit()
##        elif header=="Severity":
##            try:
##                writer=float(input(f'{header}:\t'))
##                if 1<=writer<=5:
##                    if writer != 2.5:
##                        writer=int(writer)
##                else:
##                    raise ValueError
##            except:
##                error_message(error="Severity must be a SEV number between 1-5\nHint: Make sure to just enter only the number (after SEV)")
##                add_issue()
##                return
##        elif "Short" in header:
##            writer=input(f'{header}:\t')[0:10]
##        elif header=="Issue open":
##            writer=str(yes_no("Is the issue open?")).upper()
##        elif header=="Status":
##            statuses=["Assigned","Researching","Work in Progress", "Resolved"]
##            writer=input(f'{header}:\t').capitalize()
##            try:
##                found = [ans for ans in statuses if ans.startswith(writer[0])]
##            except:
##                found=None
##            if not found:
##                error_message(error=f'Status must be any one of the following: {statuses}')
##                add_issue()
##                return
##            else:
##                if len(found)>1:
##                    found = [ans for ans in statuses if ans.startswith(writer[0:4])]
##                    if not found or len(found)>1:
##                        error_message(error=f'Status must be any one of the following: {statuses}\nHint: Must contain at least the 4 starting letters')
##                        main()
##                        exit()
##                writer=found[0]
##        else:
##            writer=input(f'{header}:\t')
##        if writer == "":
##            error_message(error="Field must not be left blank")
##            add_issue()
##            exit()
##        rowtowrite.append(writer)
##    insert_data(rowtowrite)

@app.route('/add_issue', methods=['GET', 'POST'])
def add_issue():
    if request.method == 'POST':
        rowtowrite = []
        headers = get_headers()
        
        # Process form data
        for header in headers:
            if header == 'CreateDate' or header == 'LastUpdatedDate':
                date_value = request.form.get(header)
                if not date_value:
                    error_message(error=f'{header} is required.')
                    return redirect(url_for('add_issue'))
                try:
                    date_value = getDateTimeFromISO8601String(date_value).replace(tzinfo=None).isoformat()+"Z"
                except:
                    error_message(error="Please enter a valid date in ISO8601 format.")
                    return redirect(url_for('add_issue'))
                rowtowrite.append(date_value)
                
            elif header == 'Severity':
                severity_value = request.form.get(header)
                try:
                    severity_value = float(severity_value)
                    if 1 <= severity_value <= 5:
                        severity_value = int(severity_value) if severity_value != 2.5 else severity_value
                    else:
                        raise ValueError
                except:
                    error_message(error="Severity must be a SEV number between 1-5")
                    return redirect(url_for('add_issue'))
                rowtowrite.append(severity_value)
                
            elif header == 'Issue open':
                issue_open = request.form.get(header) == 'on'
                rowtowrite.append(str(issue_open).upper())
                
            elif header == 'Status':
                status_value = request.form.get(header)
                valid_statuses = ["Assigned", "Researching", "Work in Progress", "Resolved"]
                if status_value not in valid_statuses:
                    error_message(error=f'Status must be one of {valid_statuses}')
                    return redirect(url_for('add_issue'))
                rowtowrite.append(status_value)
                
            else:
                text_value = request.form.get(header)
                if not text_value:
                    error_message(error=f'{header} is required.')
                    return redirect(url_for('add_issue'))
                rowtowrite.append(text_value)

        # Insert the new row into the database
        insert_data(rowtowrite)
        return redirect(url_for('show_issues'))

    # For GET requests, show the form
    return render_template('add_issue.html')

@app.route('/delete_issue')
def delete_issue():
    all_rows = fetch_data()
    headers = get_headers()
    if not all_rows:
        print("There are no issues left to delete, try adding some")
        return
    line_count = 0
    for row in all_rows:
        print(f'''{headers[0]} {row[0]} is issue: {row[1]}, \
and was classed as {headers[2]} {row[2]}.''')
        print(f'''Ticket {headers[3]} is {row[3]} \
and is assigned to group {row[4]} with ID {row[5]}.''')
        print(f'Ticket was created {row[6]} and was last updated on {row[7]}.')
        status= "Open" if row[8]=="TRUE" else "Closed"
        print(f'The ticket is {status} the {headers[9]} identified is {row[9]}')
        delete=yes_no(f'Delete this ticket {row[0]}?')
        delete_row(row[0]) if delete else None
@app.route('/resolve_issue')
def resolve_issue():
    all_rows = fetch_data()
    headers = get_headers()
    if not all_rows:
        print("There are no issues to resolve, please add some")
        return
    line_count = 0
    for row in all_rows:
        if row[8]=="TRUE":
            print(f'''{headers[0]} {row[0]} is issue: {row[1]}, \
and was classed as {headers[2]} {row[2]}.''')
            print(f'''Ticket {headers[3]} is {row[3]} \
and is assigned to group {row[4]} with ID {row[5]}.''')
            print(f'Ticket was created {row[6]} and was last updated on {row[7]}.')
            resolve=yes_no(f'Resolve this ticket')
            if resolve:
                update_row(row[0], '''"Issue open"''', "FALSE")
                update_row(row[0], "LastUpdatedDate",current_datetime())
                rootcause=yes_no("Do we know what the root cause is/Do we need to update the root cause?")
                if rootcause:
                    update_row(row[0], '''"Root cause"''', input("What was the root cause:\t"))
            
@app.route('/update_issue')
def update_issue():
    all_rows = fetch_data()
    headers = get_headers()
    if not all_rows:
        print("There are no issues to update, maybe add some")
        return
    line_count = 0
    for row in all_rows:
            print(f'''{headers[0]} {row[0]} is issue: {row[1]}, \
and was classed as {headers[2]} {row[2]}.''')
            wantto=yes_no(f'Do You want to update this issue {row[0]}')
            if wantto:
                for column in range(len(row)):
                    if headers[column]=="LastUpdatedDate":
                        changeto=current_datetime()
                    elif headers[column]!="Issue open":
                        changeit=yes_no(f'Do You want to change {headers[column]} it is currently {row[column]}')
                        if changeit:
                            if "Date" in headers[column]:
                                try:
                                    changeto=getDateTimeFromISO8601String(input(f'{headers[column]}:\t')).replace(tzinfo=None).isoformat()+"Z"
                                except:
                                    error_message(error="That is not a valid date, Please use the ISO8601 UTC format")
                                    main()
                                    exit()
                            elif headers[column]=="Severity5":
                                try:
                                    changeto=float(input(f'{headers[column]}:\t'))
                                    if 1<=changeto<=5:
                                        if changeto != 2.5:
                                            changeto=int(changeto)
                                    else:
                                        raise ValueError
                                except:
                                    error_message(error="Severity must be a SEV number between 1-5\nHint: Make sure to just enter only the number (after SEV)")
                                    update_issue(CSV)
                                    return
                            elif "Short" in headers[column]:
                                changeto=input(f'{headers[column]}:\t')[0:10]
                            elif headers[column]=="Status":
                                statuses=["Assigned","Researching","Work in Progress", "Resolved"]
                                changeto=input(f'{headers[column]}:\t').capitalize()
                                found = [ans for ans in statuses if ans.startswith(changeto[0])]
                                if not found:
                                    error_message(error=f'Status must be any one of the following: {statuses}')
                                    update_issue(CSV)
                                    return
                                else:
                                    if len(found)>1:
                                        found = [ans for ans in statuses if ans.startswith(changeto[0:4])]
                                        if not found or len(found)>1:
                                            error_message(error=f'Status must be any one of the following: {statuses}\nHint: Must contain at least the 4 starting letters')
                                            main()
                                            exit()
                                    changeto=found[0]
                            else:
                                changeto=input(f'{headers[column]}:\t')
                            if changeto == "":
                                error_message(error="Field must not be left blank")
                                update_issue()
                                return
                            update_row(row[0],headers[column],changeto)
@app.route('/find_issue')
def find_issue():
    issue=input("Search:\t")
    query = f'''SELECT * FROM data WHERE ShortId LIKE ? OR Title LIKE ? OR Severity LIKE ? OR Status LIKE ? OR AssignedGroup LIKE ? OR AssigneeIdentity LIKE ? OR "Root cause" LIKE ?'''
    search_term = f"%{issue}%"
    cursor.execute(query, (search_term, search_term, search_term, search_term, search_term, search_term, search_term))
    matching_rows = cursor.fetchall()
    headers = get_headers()
    if not matching_rows:
        print("No issues found matching that search, check Your input and try again.")
        return
    line_count = 0
    for row in matching_rows:    
            print(f'''{headers[0]} {row[0]} is issue: {row[1]}, \
and was classed as {headers[2]} {row[2]}.''')
            print(f'''Ticket {headers[3]} is {row[3]} \
and is assigned to group {row[4]} with ID {row[5]}.''')
            print(f'Ticket was created {row[6]} and was last updated on {row[7]}.')
            status= "Open" if row[8]=="TRUE" else "Closed"
            print(f'The ticket is {status} the {headers[9]} identified is {row[9]}')
            line_count += 1
            try:
                if row[10]:
                    print(f"Additional information includes: {row[10:]}")
            except:
                continue
    print(f'Processed {line_count} lines.')

@app.route('/')
def menu():
    return render_template('menu.html')

if __name__ == '__main__':
    app.run()
