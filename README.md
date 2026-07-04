# CIS Compliance Audit Platform

A complete, full-stack cybersecurity auditing platform designed to check Windows 11 and Linux systems against CIS Benchmarks. 
Built using React, FastAPI, and MongoDB.

## Features
- **Secure Authentication**: JWT-based authentication with bcrypt password hashing.
- **System Management**: Register systems (Windows/Linux) to be audited.
- **Audit Execution**: Trigger mock execution of PowerShell/Bash audit scripts.
- **Local Auditor**: Download a lightweight script for Windows or Linux, run it locally as Administrator/Root, and upload the JSON audit payload back to the API.
- **Dashboard**: Visual summary of compliance scores and recent audits.
- **Report Generation**: Export audit results as JSON or CSV.

## Local Auditor Script Usage
The backend provides downloadable scripts at:
- `GET /api/audits/download-script/linux`
- `GET /api/audits/download-script/windows`

Run the script locally with admin/root privileges and provide:
- `--api-url` - backend API base URL
- `--token` - authenticated JWT token
- `--hostname` - system hostname
- `--operating_system` - `linux` or `windows`
- `--ip_address` - system IP address

The script will automatically POST the audit JSON payload to `/api/audits/upload`.

## Technologies Used
- **Frontend**: React.js, React Router, Context API, Bootstrap 5, Axios.
- **Backend**: FastAPI (Python), Motor (Async MongoDB), Passlib, PyJWT.
- **Database**: MongoDB.
- **Scripts**: PowerShell (Windows), Bash (Linux).

## Folder Structure
```text
cis-compliance-platform/
│
├── backend/                  # FastAPI Application
│   ├── app/                  
│   │   ├── api/              # Route handlers
│   │   ├── authentication/   # JWT and Hashing logic
│   │   ├── database/         # MongoDB connection
│   │   ├── models/           # Pydantic models
│   │   ├── schemas/          # API Request/Response schemas
│   │   └── config.py         # Environment configuration
│   ├── main.py               # Entry point
│   ├── requirements.txt      # Python dependencies
│   └── .env                  # Environment Variables
│
├── frontend/                 # React Application
│   ├── src/
│   │   ├── components/       # Reusable UI (Navbar, Sidebar)
│   │   ├── context/          # State management (AuthContext)
│   │   ├── pages/            # View components (Login, Dashboard)
│   │   ├── services/         # Axios wrapper
│   │   ├── App.jsx           # Routing
│   │   └── main.jsx          # Entry point
│   └── package.json          # Node dependencies
│
└── audit_scripts/            # System Auditing Scripts
    ├── windows/
    │   └── audit.ps1
    └── linux/
        └── audit.sh
```

## Setup Instructions

### 1. Database (MongoDB)
Ensure you have MongoDB Community Edition running locally on port `27017`.

### 2. Backend Setup
```bash
cd backend
python -m venv venv
# Activate venv: `venv\Scripts\activate` on Windows or `source venv/bin/activate` on Mac/Linux
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```
The backend will run on `http://localhost:8000`. API docs available at `http://localhost:8000/docs`.

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
The frontend will run on `http://localhost:5173`.

### 4. Project Root Run
If you want to run both backend and frontend together from the project root:
```bash
npm install -g concurrently
npm install
npm run dev
```

## Educational Notes for Beginners
- **Clean Architecture**: Notice how the backend is divided into `routes`, `schemas`, and `models`. This separation of concerns makes the code easier to test and maintain.
- **Context API**: Check `AuthContext.jsx` to see how user state is managed globally without prop drilling.
- **Security**: Look at `hash.py` and `jwt.py` to understand how passwords are never stored in plain text and how stateless sessions are maintained.
