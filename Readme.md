# 🏥 Hospital Management System

A complete, professional Hospital Management System built with Flask, MySQL, and Bootstrap. This system provides comprehensive patient, doctor, and appointment management with a modern, responsive interface.

## 📋 Table of Contents

- [Features](#features)
- [Technology Stack](#technology-stack)
- [Installation](#installation)
- [Database Setup](#database-setup)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [API Endpoints](#api-endpoints)
- [Contributing](#contributing)
- [License](#license)

## ✨ Features

### 🔐 Authentication & Security
- Secure admin login with session management
- Password hashing using SHA-256
- Session-based authentication
- Automatic logout functionality

### 👥 Patient Management
- Complete patient registration system
- Patient search and filtering
- Detailed patient profiles
- Medical history tracking
- Contact information management

### 👨‍⚕️ Doctor Management
- Doctor registration and profiles
- Specialization categorization
- Experience and fee tracking
- Doctor filtering by specialization

### 📅 Appointment System
- Appointment scheduling interface
- Patient-doctor relationship management
- Appointment status tracking
- Date-based filtering
- Fee calculation and tracking

### 📊 Dashboard & Analytics
- Real-time statistics dashboard
- Total patients, doctors, appointments
- Income tracking and reporting
- Today's appointments overview

### 📄 PDF Reports
- Downloadable patient reports
- Appointment history reports
- Professional PDF formatting
- Date-stamped documents

### 🎨 Modern UI/UX
- Responsive Bootstrap 5 design
- Professional color scheme
- Interactive cards and modals
- Mobile-friendly interface
- Intuitive navigation

## 🛠 Technology Stack

- **Backend**: Python Flask 2.3.3
- **Database**: MySQL 8.0+
- **Frontend**: HTML5, CSS3, Bootstrap 5
- **PDF Generation**: xhtml2pdf
- **Database Connector**: mysql-connector-python
- **Icons**: Bootstrap Icons

## 🚀 Installation

### Prerequisites

- Python 3.8 or higher
- MySQL 8.0 or higher
- pip (Python package installer)

### Step 1: Clone or Download

\`\`\`bash
# Create project directory
mkdir hospital-management
cd hospital-management
\`\`\`

### Step 2: Install Dependencies

\`\`\`bash
# Install required Python packages
pip install flask mysql-connector-python xhtml2pdf
\`\`\`

### Step 3: Create Project Files

Create the following folder structure and copy the provided code files:

\`\`\`
hospital-management/
├── app.py
├── requirements.txt
├── README.md
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   ├── patients.html
│   ├── add_patient.html
│   ├── doctors.html
│   ├── add_doctor.html
│   ├── appointments.html
│   ├── add_appointment.html
│   ├── pdf_patients.html
│   └── pdf_appointments.html
└── scripts/
    └── create_database.sql
\`\`\`

## 🗄 Database Setup

### Step 1: Create MySQL Database

\`\`\`sql
-- Connect to MySQL and run:
CREATE DATABASE hms;
\`\`\`

### Step 2: Run Database Script

\`\`\`bash
# In MySQL command line or MySQL Workbench:
mysql -u your_username -p hms < scripts/create_database.sql
\`\`\`

### Step 3: Update Database Configuration

Edit `app.py` and update the database configuration:

```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'your_mysql_username',
    'password': 'your_mysql_password',
    'database': 'hms'
}
