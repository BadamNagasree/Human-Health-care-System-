#  Human Healthcare Management System

A full-stack healthcare web application built using **Flask + MySQL** that allows patients to book appointments, manage medical records, and interact with doctors and admin.

---

##  Features

###  User (Patient)
- Register & Login system
- Book appointments with doctors
- View & cancel appointments
- Maintain medical records:
  - Age
  - Blood Pressure (BP)
  - Diseases
  - Medicines
- Update & delete medical reports

---

### Admin Panel
- Add new doctors
- Delete doctors
- View all appointments

---

### Appointment System
- Book appointments
- Track appointment status
- View appointment history

---

## Tech Stack

- **Backend:** Python (Flask)
- **Database:** MySQL
- **Frontend:** HTML, CSS (Modern UI)
- **Authentication:** Werkzeug (Password Hashing)

---

## Project Structure
project/
│
├── app.py
├── templates/
│ ├── login.html
│ ├── register.html
│ ├── dashboard.html
│ ├── book.html
│ ├── appointments.html
│ ├── reports.html
│ ├── admin.html
│ ├── admin_doctors.html
│ └── admin_appointments.html
│
├── static/
│ ├── style.css
│ ├── dashboard.css
│ └── appointments.css
│
└── README.md

---

##  Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/BadamNagasree/Human-Health-care-System-.git
cd healthcare-system
pip install flask mysql-connector-python werkzeug
python app.py
