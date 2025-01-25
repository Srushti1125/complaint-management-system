from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a strong secret key

# Database connection
mydb = mysql.connector.connect(
    host="localhost",
    port="3306",
    user="root",
    password="mySQL@2915",
    database="complaintmanagement"
)

# Route for Home Page
@app.route('/')
def home():
    return render_template('index.html')

# Citizen Login
@app.route('/citizen_login', methods=['GET', 'POST'])
def citizen_login():
    if request.method == 'POST':
        aadhar_id = request.form['aadhar_id']
        password = request.form['password']
        cursor = mydb.cursor()
        cursor.execute("SELECT * FROM Citizen WHERE AadharID = %s AND Password = %s", (aadhar_id, password))
        user = cursor.fetchone()
        cursor.close()
        if user:
            session['aadhar_id'] = aadhar_id
            return redirect(url_for('complaint_form'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')
    return render_template('citizen_login.html')

# User Registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        aadhar_id = request.form['aadhar_id']
        name = request.form['name']
        age = request.form['age']
        address = request.form['address']
        contact_no = request.form['contact_no']
        password = request.form['password']
        cursor = mydb.cursor()
        cursor.execute(
            "INSERT INTO Citizen (AadharID, Name, Age, Address, ContactNo, Password) VALUES (%s, %s, %s, %s, %s, %s)",
            (aadhar_id, name, age, address, contact_no, password)
        )
        mydb.commit()
        cursor.close()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('citizen_login'))
    return render_template('register.html')

# Department Login
@app.route('/department_login', methods=['GET', 'POST'])
def department_login():
    if request.method == 'POST':
        department_id = request.form['department_id']
        password = request.form['password']
        cursor = mydb.cursor()
        cursor.execute("SELECT * FROM Department WHERE DepartmentID = %s AND password = %s", (department_id, password))
        department = cursor.fetchone()
        cursor.close()
        if department:
            session['department_id'] = department_id
            return redirect(url_for('view_all_complaints'))
        else:
            flash('Invalid department credentials.', 'danger')
    return render_template('department_login.html')

# Complaint Form
@app.route('/complaint_form', methods=['GET', 'POST'])
def complaint_form():
    if 'aadhar_id' not in session:
        return redirect(url_for('citizen_login'))
    cursor = mydb.cursor(dictionary=True)
    cursor.execute("SELECT DepartmentID, SubDepartment FROM Department")
    departments = cursor.fetchall()
    cursor.close()
    if request.method == 'POST':
        complaint_type = request.form['complaint_type']
        description = request.form['description']
        complaint_date = request.form['complaint_date']
        department_id = request.form['department_id']
        location = request.form['location']
        cursor = mydb.cursor()
        cursor.execute(
            "INSERT INTO Complaint (ComplaintType, Description, ComplaintDate, DepartmentID, AadharID, Location) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (complaint_type, description, complaint_date, department_id, session['aadhar_id'], location)
        )
        complaint_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO ComplaintStatus (ComplaintDate, Status, ComplaintID) "
            "VALUES (%s, %s, %s)",
            (complaint_date, 'unresolved', complaint_id)
        )
        mydb.commit()
        cursor.close()
        flash('Complaint submitted successfully!', 'success')
        return redirect(url_for('complaint_form'))
    return render_template('complaint_form.html', departments=departments)

# Complaint Status View for Citizen
@app.route('/status')
def status():
    if 'aadhar_id' not in session:
        return redirect(url_for('citizen_login'))
    cursor = mydb.cursor(dictionary=True)
    cursor.execute("""
        SELECT c.ComplaintID, c.ComplaintType, c.Description, c.ComplaintDate, cs.Status
        FROM Complaint c
        JOIN ComplaintStatus cs ON c.ComplaintID = cs.ComplaintID
        WHERE c.AadharID = %s
    """, (session['aadhar_id'],))
    complaints = cursor.fetchall()
    cursor.close()
    return render_template('status.html', complaints=complaints)

# Route for Department to View All Complaints
@app.route('/view_all_complaints', methods=['GET'])
def view_all_complaints():
    if 'department_id' not in session:
        return redirect(url_for('department_login'))
    
    cursor = mydb.cursor(dictionary=True)
    cursor.execute("""
        SELECT c.ComplaintID, c.ComplaintType, c.Description, c.ComplaintDate, c.Location, cs.Status
        FROM Complaint c
        JOIN ComplaintStatus cs ON c.ComplaintID = cs.ComplaintID
        WHERE c.DepartmentID = %s
    """, (session['department_id'],))
    complaints = cursor.fetchall()
    cursor.close()
    
    return render_template('view_all_complaints.html', complaints=complaints)

# Update Complaint Status by Department
@app.route('/update_status', methods=['GET', 'POST'])
def update_status():
    if 'department_id' not in session:
        return redirect(url_for('department_login'))
    cursor = mydb.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Complaint WHERE DepartmentID = %s", (session['department_id'],))
    complaints = cursor.fetchall()
    cursor.close()
    if request.method == 'POST':
        complaint_id = request.form['complaint_id']
        status = request.form['status_id']
        resolution_date = request.form['resolution_date']
        cursor = mydb.cursor()
        cursor.execute("UPDATE ComplaintStatus SET Status = %s, ResolutionDate = %s WHERE ComplaintID = %s",
                      (status, resolution_date, complaint_id))
        mydb.commit()
        cursor.close()
        flash('Complaint status updated successfully!', 'success')
        return render_template('update_status.html', complaints=complaints)
    return render_template('update_status.html', complaints=complaints)


# Logout
@app.route('/logout')
def logout():
    session.pop('aadhar_id', None)
    session.pop('department_id', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)