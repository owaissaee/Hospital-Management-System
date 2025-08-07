"""
Hospital Management System - Main Flask Application
Author: HMS Development Team
Description: Complete hospital management system with patient, doctor, and appointment management
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response
import mysql.connector
from mysql.connector import Error
from datetime import datetime, date
import hashlib
from xhtml2pdf import pisa
import io

# Initialize Flask application
app = Flask(__name__)
app.secret_key = 'your_secret_key_here_change_this_in_production'  # Change this in production!

# Database configuration - Updated to match your HMS database
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',  # Replace with your MySQL username
    'password': 'mysql',  # Replace with your MySQL password
    'database': 'HMS',  # Changed to uppercase to match your database
    'autocommit': True,
    'raise_on_warnings': True
}

def get_db_connection():
    """
    Create and return a database connection
    Returns: MySQL connection object or None if connection fails
    """
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            print("Successfully connected to MySQL database")
            return connection
    except mysql.connector.Error as e:
        print(f"Error connecting to MySQL: {e}")
        if e.errno == mysql.connector.errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif e.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(f"MySQL Error: {e}")
    except Exception as e:
        print(f"General error: {e}")
    return None

def hash_password(password):
    """
    Hash password using SHA-256
    Args: password (str): Plain text password
    Returns: str: Hashed password
    """
    return hashlib.sha256(password.encode()).hexdigest()

@app.route('/')
def index():
    """
    Home route - redirects to login if not authenticated, otherwise to dashboard
    """
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/test-db')
def test_db():
    """
    Test database connection - Remove this in production
    """
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            cursor.close()
            connection.close()
            return f"Database connection successful! Test query result: {result}"
        except Error as e:
            return f"Database connected but query failed: {e}"
    else:
        return "Database connection failed!"

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Login route - handles user authentication
    GET: Display login form
    POST: Process login credentials
    """
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = hash_password(password)
        
        # Connect to database and verify credentials
        connection = get_db_connection()
        if connection:
            try:
                cursor = connection.cursor(dictionary=True)
                query = "SELECT * FROM staff WHERE username = %s AND password = %s AND role = 'Admin'"
                cursor.execute(query, (username, hashed_password))
                user = cursor.fetchone()
                
                if user:
                    # Login successful - create session
                    session['user_id'] = user['id']
                    session['username'] = user['username']
                    flash('Login successful!', 'success')
                    return redirect(url_for('dashboard'))
                else:
                    flash('Invalid username or password!', 'error')
                    
            except Error as e:
                flash(f'Database error: {e}', 'error')
            finally:
                cursor.close()
                connection.close()
        else:
            flash('Database connection failed!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """
    Logout route - clears session and redirects to login
    """
    session.clear()
    flash('You have been logged out successfully!', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    """
    Dashboard route - displays system statistics
    Requires authentication
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    connection = get_db_connection()
    stats = {
        'total_patients': 0,
        'total_doctors': 0,
        'today_appointments': 0,
        'total_income': 0
    }
    
    if connection:
        try:
            cursor = connection.cursor()
            
            # Get total patients
            cursor.execute("SELECT COUNT(*) FROM patients")
            stats['total_patients'] = cursor.fetchone()[0]
            
            # Get total doctors
            cursor.execute("SELECT COUNT(*) FROM doctors")
            stats['total_doctors'] = cursor.fetchone()[0]
            
            # Get today's appointments
            today = date.today()
            cursor.execute("SELECT COUNT(*) FROM appointments WHERE DATE(appointment_date) = %s", (today,))
            stats['today_appointments'] = cursor.fetchone()[0]
            
            # Get total income (sum of all appointment fees)
            cursor.execute("SELECT SUM(fee) FROM appointments")
            result = cursor.fetchone()[0]
            stats['total_income'] = result if result else 0
            
        except Error as e:
            flash(f'Error fetching dashboard data: {e}', 'error')
        finally:
            cursor.close()
            connection.close()
    
    return render_template('dashboard.html', stats=stats)

@app.route('/patients')
def patients():
    """
    Patients list route - displays all patients with search functionality
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    search = request.args.get('search', '')
    patients_list = []
    
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            if search:
                query = "SELECT * FROM patients WHERE name LIKE %s OR phone LIKE %s ORDER BY name"
                cursor.execute(query, (f'%{search}%', f'%{search}%'))
            else:
                cursor.execute("SELECT * FROM patients ORDER BY name")
            patients_list = cursor.fetchall()
            
        except Error as e:
            flash(f'Error fetching patients: {e}', 'error')
        finally:
            cursor.close()
            connection.close()
    
    return render_template('patients.html', patients=patients_list, search=search)

@app.route('/add_patient', methods=['GET', 'POST'])
def add_patient():
    """
    Add patient route - handles patient registration
    GET: Display patient registration form
    POST: Process patient registration
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Get form data
        name = request.form['name']
        age = request.form['age']
        gender = request.form['gender']
        phone = request.form['phone']
        email = request.form['email']
        address = request.form['address']
        medical_history = request.form['medical_history']
        
        # Insert into database
        connection = get_db_connection()
        if connection:
            try:
                cursor = connection.cursor()
                query = """INSERT INTO patients (name, age, gender, phone, email, address, medical_history) 
                          VALUES (%s, %s, %s, %s, %s, %s, %s)"""
                cursor.execute(query, (name, age, gender, phone, email, address, medical_history))
                connection.commit()
                flash('Patient added successfully!', 'success')
                return redirect(url_for('patients'))
                
            except Error as e:
                flash(f'Error adding patient: {e}', 'error')
            finally:
                cursor.close()
                connection.close()
    
    return render_template('add_patient.html')

@app.route('/edit_patient/<int:patient_id>', methods=['GET', 'POST'])
def edit_patient(patient_id):
    """
    Edit patient route - handles patient information updates
    GET: Display patient edit form
    POST: Process patient updates
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    connection = get_db_connection()
    patient = None
    
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            
            if request.method == 'POST':
                # Get form data
                name = request.form['name']
                age = request.form['age']
                gender = request.form['gender']
                phone = request.form['phone']
                email = request.form['email']
                address = request.form['address']
                medical_history = request.form['medical_history']
                
                # Update patient in database
                query = """UPDATE patients SET name = %s, age = %s, gender = %s, phone = %s, 
                          email = %s, address = %s, medical_history = %s WHERE id = %s"""
                cursor.execute(query, (name, age, gender, phone, email, address, medical_history, patient_id))
                connection.commit()
                flash('Patient updated successfully!', 'success')
                return redirect(url_for('patients'))
            else:
                # Get patient data for form
                cursor.execute("SELECT * FROM patients WHERE id = %s", (patient_id,))
                patient = cursor.fetchone()
                
                if not patient:
                    flash('Patient not found!', 'error')
                    return redirect(url_for('patients'))
                    
        except Error as e:
            flash(f'Error updating patient: {e}', 'error')
        finally:
            cursor.close()
            connection.close()
    
    return render_template('edit_patient.html', patient=patient)

@app.route('/delete_patient/<int:patient_id>')
def delete_patient(patient_id):
    """
    Delete patient route - removes patient from database
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM patients WHERE id = %s", (patient_id,))
            connection.commit()
            
            if cursor.rowcount > 0:
                flash('Patient deleted successfully!', 'success')
            else:
                flash('Patient not found!', 'error')
                
        except Error as e:
            flash(f'Error deleting patient: {e}', 'error')
        finally:
            cursor.close()
            connection.close()
    
    return redirect(url_for('patients'))

@app.route('/doctors')
def doctors():
    """
    Doctors list route - displays all doctors with specialization filter
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    specialization = request.args.get('specialization', '')
    doctors_list = []
    specializations = []
    
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            
            # Get all specializations for filter dropdown
            cursor.execute("SELECT DISTINCT specialization FROM doctors ORDER BY specialization")
            specializations = [row['specialization'] for row in cursor.fetchall()]
            
            # Get doctors based on filter
            if specialization:
                query = "SELECT * FROM doctors WHERE specialization = %s ORDER BY name"
                cursor.execute(query, (specialization,))
            else:
                cursor.execute("SELECT * FROM doctors ORDER BY name")
            doctors_list = cursor.fetchall()
            
        except Error as e:
            flash(f'Error fetching doctors: {e}', 'error')
        finally:
            cursor.close()
            connection.close()
    
    return render_template('doctors.html', doctors=doctors_list, specializations=specializations, selected_specialization=specialization)

@app.route('/add_doctor', methods=['GET', 'POST'])
def add_doctor():
    """
    Add doctor route - handles doctor registration
    GET: Display doctor registration form
    POST: Process doctor registration
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Get form data
        name = request.form['name']
        specialization = request.form['specialization']
        phone = request.form['phone']
        email = request.form['email']
        experience = request.form['experience']
        fee = request.form['fee']
        
        # Insert into database
        connection = get_db_connection()
        if connection:
            try:
                cursor = connection.cursor()
                query = """INSERT INTO doctors (name, specialization, phone, email, experience, fee) 
                          VALUES (%s, %s, %s, %s, %s, %s)"""
                cursor.execute(query, (name, specialization, phone, email, experience, fee))
                connection.commit()
                flash('Doctor added successfully!', 'success')
                return redirect(url_for('doctors'))
                
            except Error as e:
                flash(f'Error adding doctor: {e}', 'error')
            finally:
                cursor.close()
                connection.close()
    
    return render_template('add_doctor.html')

@app.route('/edit_doctor/<int:doctor_id>', methods=['GET', 'POST'])
def edit_doctor(doctor_id):
    """
    Edit doctor route - handles doctor information updates
    GET: Display doctor edit form
    POST: Process doctor updates
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    connection = get_db_connection()
    doctor = None
    
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            
            if request.method == 'POST':
                # Get form data
                name = request.form['name']
                specialization = request.form['specialization']
                phone = request.form['phone']
                email = request.form['email']
                experience = request.form['experience']
                fee = request.form['fee']
                
                # Update doctor in database
                query = """UPDATE doctors SET name = %s, specialization = %s, phone = %s, 
                          email = %s, experience = %s, fee = %s WHERE id = %s"""
                cursor.execute(query, (name, specialization, phone, email, experience, fee, doctor_id))
                connection.commit()
                flash('Doctor updated successfully!', 'success')
                return redirect(url_for('doctors'))
            else:
                # Get doctor data for form
                cursor.execute("SELECT * FROM doctors WHERE id = %s", (doctor_id,))
                doctor = cursor.fetchone()
                
                if not doctor:
                    flash('Doctor not found!', 'error')
                    return redirect(url_for('doctors'))
                    
        except Error as e:
            flash(f'Error updating doctor: {e}', 'error')
        finally:
            cursor.close()
            connection.close()
    
    return render_template('edit_doctor.html', doctor=doctor)

@app.route('/delete_doctor/<int:doctor_id>')
def delete_doctor(doctor_id):
    """
    Delete doctor route - removes doctor from database
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM doctors WHERE id = %s", (doctor_id,))
            connection.commit()
            
            if cursor.rowcount > 0:
                flash('Doctor deleted successfully!', 'success')
            else:
                flash('Doctor not found!', 'error')
                
        except Error as e:
            flash(f'Error deleting doctor: {e}', 'error')
        finally:
            cursor.close()
            connection.close()
    
    return redirect(url_for('doctors'))

@app.route('/appointments')
def appointments():
    """
    Appointments list route - displays all appointments with date filter
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    date_filter = request.args.get('date', '')
    appointments_list = []
    
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            if date_filter:
                query = """SELECT a.*, p.name as patient_name, d.name as doctor_name, d.specialization as doctor_specialization
                          FROM appointments a 
                          JOIN patients p ON a.patient_id = p.id 
                          JOIN doctors d ON a.doctor_id = d.id 
                          WHERE DATE(a.appointment_date) = %s 
                          ORDER BY a.appointment_date DESC"""
                cursor.execute(query, (date_filter,))
            else:
                query = """SELECT a.*, p.name as patient_name, d.name as doctor_name, d.specialization as doctor_specialization
                          FROM appointments a 
                          JOIN patients p ON a.patient_id = p.id 
                          JOIN doctors d ON a.doctor_id = d.id 
                          ORDER BY a.appointment_date DESC"""
                cursor.execute(query)
            appointments_list = cursor.fetchall()
            
        except Error as e:
            flash(f'Error fetching appointments: {e}', 'error')
        finally:
            cursor.close()
            connection.close()
    
    return render_template('appointments.html', appointments=appointments_list, date_filter=date_filter)

@app.route('/add_appointment', methods=['GET', 'POST'])
def add_appointment():
    """
    Add appointment route - handles appointment scheduling
    GET: Display appointment form with patient and doctor lists
    POST: Process appointment scheduling
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    patients_list = []
    doctors_list = []
    
    # Get patients and doctors for dropdowns
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT id, name, age FROM patients ORDER BY name")
            patients_list = cursor.fetchall()
            cursor.execute("SELECT id, name, specialization, fee FROM doctors ORDER BY name")
            doctors_list = cursor.fetchall()
        except Error as e:
            flash(f'Error fetching data: {e}', 'error')
        finally:
            cursor.close()
            connection.close()
    
    if request.method == 'POST':
        # Get form data
        patient_id = request.form['patient_id']
        doctor_id = request.form['doctor_id']
        appointment_date = request.form['appointment_date']
        appointment_time = request.form['appointment_time']
        fee = request.form['fee']
        notes = request.form['notes']
        
        # Combine date and time
        appointment_datetime = f"{appointment_date} {appointment_time}"
        
        # Insert into database
        connection = get_db_connection()
        if connection:
            try:
                cursor = connection.cursor()
                query = """INSERT INTO appointments (patient_id, doctor_id, appointment_date, fee, notes) 
                          VALUES (%s, %s, %s, %s, %s)"""
                cursor.execute(query, (patient_id, doctor_id, appointment_datetime, fee, notes))
                connection.commit()
                flash('Appointment scheduled successfully!', 'success')
                return redirect(url_for('appointments'))
                
            except Error as e:
                flash(f'Error scheduling appointment: {e}', 'error')
            finally:
                cursor.close()
                connection.close()
    
    return render_template('add_appointment.html', patients=patients_list, doctors=doctors_list)

@app.route('/edit_appointment/<int:appointment_id>', methods=['GET', 'POST'])
def edit_appointment(appointment_id):
    """
    Edit appointment route - handles appointment updates
    GET: Display appointment edit form
    POST: Process appointment updates
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    patients_list = []
    doctors_list = []
    appointment = None
    
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            
            # Get patients and doctors for dropdowns
            cursor.execute("SELECT id, name, age FROM patients ORDER BY name")
            patients_list = cursor.fetchall()
            cursor.execute("SELECT id, name, specialization, fee FROM doctors ORDER BY name")
            doctors_list = cursor.fetchall()
            
            if request.method == 'POST':
                # Get form data
                patient_id = request.form['patient_id']
                doctor_id = request.form['doctor_id']
                appointment_date = request.form['appointment_date']
                appointment_time = request.form['appointment_time']
                fee = request.form['fee']
                status = request.form['status']
                notes = request.form['notes']
                
                # Combine date and time
                appointment_datetime = f"{appointment_date} {appointment_time}"
                
                # Update appointment in database
                query = """UPDATE appointments SET patient_id = %s, doctor_id = %s, appointment_date = %s, 
                          fee = %s, status = %s, notes = %s WHERE id = %s"""
                cursor.execute(query, (patient_id, doctor_id, appointment_datetime, fee, status, notes, appointment_id))
                connection.commit()
                flash('Appointment updated successfully!', 'success')
                return redirect(url_for('appointments'))
            else:
                # Get appointment data for form
                query = """SELECT a.*, p.name as patient_name, d.name as doctor_name 
                          FROM appointments a 
                          JOIN patients p ON a.patient_id = p.id 
                          JOIN doctors d ON a.doctor_id = d.id 
                          WHERE a.id = %s"""
                cursor.execute(query, (appointment_id,))
                appointment = cursor.fetchone()
                
                if not appointment:
                    flash('Appointment not found!', 'error')
                    return redirect(url_for('appointments'))
                    
        except Error as e:
            flash(f'Error updating appointment: {e}', 'error')
        finally:
            cursor.close()
            connection.close()
    
    return render_template('edit_appointment.html', appointment=appointment, patients=patients_list, doctors=doctors_list)

@app.route('/complete_appointment/<int:appointment_id>')
def complete_appointment(appointment_id):
    """
    Mark appointment as complete
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            query = "UPDATE appointments SET status = 'Completed' WHERE id = %s"
            cursor.execute(query, (appointment_id,))
            connection.commit()
            
            if cursor.rowcount > 0:
                flash('Appointment marked as completed!', 'success')
            else:
                flash('Appointment not found!', 'error')
                
        except Error as e:
            flash(f'Error updating appointment: {e}', 'error')
        finally:
            cursor.close()
            connection.close()
    
    return redirect(url_for('appointments'))

@app.route('/cancel_appointment/<int:appointment_id>')
def cancel_appointment(appointment_id):
    """
    Mark appointment as cancelled
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            query = "UPDATE appointments SET status = 'Cancelled' WHERE id = %s"
            cursor.execute(query, (appointment_id,))
            connection.commit()
            
            if cursor.rowcount > 0:
                flash('Appointment cancelled!', 'info')
            else:
                flash('Appointment not found!', 'error')
                
        except Error as e:
            flash(f'Error updating appointment: {e}', 'error')
        finally:
            cursor.close()
            connection.close()
    
    return redirect(url_for('appointments'))

@app.route('/delete_appointment/<int:appointment_id>')
def delete_appointment(appointment_id):
    """
    Delete appointment route - removes appointment from database
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM appointments WHERE id = %s", (appointment_id,))
            connection.commit()
            
            if cursor.rowcount > 0:
                flash('Appointment deleted successfully!', 'success')
            else:
                flash('Appointment not found!', 'error')
                
        except Error as e:
            flash(f'Error deleting appointment: {e}', 'error')
        finally:
            cursor.close()
            connection.close()
    
    return redirect(url_for('appointments'))

@app.route('/download_patients_pdf')
def download_patients_pdf():
    """
    Generate and download PDF report of all patients
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    patients_list = []
    connection = get_db_connection()
    
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM patients ORDER BY name")
            patients_list = cursor.fetchall()
        except Error as e:
            flash(f'Error fetching patients: {e}', 'error')
            return redirect(url_for('patients'))
        finally:
            cursor.close()
            connection.close()
    
    # Render HTML template for PDF
    html = render_template('pdf_patients.html', patients=patients_list, date=datetime.now().strftime('%Y-%m-%d'))
    
    # Create PDF
    pdf_buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=pdf_buffer)
    
    if pisa_status.err:
        flash('Error generating PDF', 'error')
        return redirect(url_for('patients'))
    
    pdf_buffer.seek(0)
    response = make_response(pdf_buffer.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=patients_report_{datetime.now().strftime("%Y%m%d")}.pdf'
    
    return response

@app.route('/download_appointments_pdf')
def download_appointments_pdf():
    """
    Generate and download PDF report of all appointments
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    appointments_list = []
    connection = get_db_connection()
    
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            query = """SELECT a.*, p.name as patient_name, d.name as doctor_name 
                      FROM appointments a 
                      JOIN patients p ON a.patient_id = p.id 
                      JOIN doctors d ON a.doctor_id = d.id 
                      ORDER BY a.appointment_date DESC"""
            cursor.execute(query)
            appointments_list = cursor.fetchall()
        except Error as e:
            flash(f'Error fetching appointments: {e}', 'error')
            return redirect(url_for('appointments'))
        finally:
            cursor.close()
            connection.close()
    
    # Render HTML template for PDF
    html = render_template('pdf_appointments.html', appointments=appointments_list, date=datetime.now().strftime('%Y-%m-%d'))
    
    # Create PDF
    pdf_buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=pdf_buffer)
    
    if pisa_status.err:
        flash('Error generating PDF', 'error')
        return redirect(url_for('appointments'))
    
    pdf_buffer.seek(0)
    response = make_response(pdf_buffer.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=appointments_report_{datetime.now().strftime("%Y%m%d")}.pdf'
    
    return response

@app.route('/create-admin')
def create_admin():
    """
    Create admin user - Remove this in production
    """
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            
            # Check if admin user already exists
            cursor.execute("SELECT * FROM staff WHERE username = 'admin'")
            existing_user = cursor.fetchone()
            
            if existing_user:
                return f"Admin user already exists! Password hash in DB: {existing_user['password']}"
            
            # Create admin user with hashed password
            username = 'admin'
            password = 'admin123'
            hashed_password = hash_password(password)
            
            query = """INSERT INTO staff (username, password, role, name, email, phone) 
                      VALUES (%s, %s, %s, %s, %s, %s)"""
            cursor.execute(query, (username, hashed_password, 'Admin', 'System Administrator', 'admin@hospital.com', '(555) 000-0001'))
            connection.commit()
            
            return f"Admin user created successfully!<br>Username: {username}<br>Password: {password}<br>Hash: {hashed_password}"
            
        except Error as e:
            return f"Error creating admin user: {e}"
        finally:
            cursor.close()
            connection.close()
    else:
        return "Database connection failed!"

@app.route('/check-users')
def check_users():
    """
    Check existing users in database - Remove this in production
    """
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT id, username, role, name FROM staff")
            users = cursor.fetchall()
            
            result = "<h3>Existing Users:</h3>"
            for user in users:
                result += f"<p>ID: {user['id']}, Username: {user['username']}, Role: {user['role']}, Name: {user['name']}</p>"
            
            if not users:
                result += "<p>No users found in database!</p>"
                
            return result
            
        except Error as e:
            return f"Error fetching users: {e}"
        finally:
            cursor.close()
            connection.close()
    else:
        return "Database connection failed!"

@app.route('/reset-admin-password')
def reset_admin_password():
    """
    Reset admin password - Remove this in production
    """
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            
            # Reset admin password to 'admin123'
            new_password = 'admin123'
            hashed_password = hash_password(new_password)
            
            query = "UPDATE staff SET password = %s WHERE username = 'admin'"
            cursor.execute(query, (hashed_password,))
            connection.commit()
            
            if cursor.rowcount > 0:
                return f"Admin password reset successfully!<br>Username: admin<br>Password: {new_password}"
            else:
                return "No admin user found to update!"
                
        except Error as e:
            return f"Error resetting password: {e}"
        finally:
            cursor.close()
            connection.close()
    else:
        return "Database connection failed!"

if __name__ == '__main__':
    """
    Run the Flask application
    Debug mode is enabled for development - disable in production
    """
    app.run(debug=True, host='0.0.0.0', port=5000)
