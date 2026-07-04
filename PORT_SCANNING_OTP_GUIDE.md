# TCP Port Scanning & Email OTP Verification Implementation

## Overview
Enhanced the CIS Audit Platform with two major security features:
1. **TCP Port Scanning** - Scan open ports on registered systems
2. **Email Verification with OTP** - Secure email verification during registration

---

## 1. Email Verification with OTP

### Features
- **OTP Generation**: 6-digit random code generated during registration
- **Email Delivery**: OTP sent via SMTP with HTML-formatted email
- **Expiration**: OTP expires in 10 minutes
- **Verification**: Users verify email before full account activation
- **Resend Option**: Users can request new OTP if expired

### Backend Implementation

#### New Files
- `backend/app/security/email_otp.py` - Email and OTP utilities
  - `generate_otp()` - Creates 6-digit random code
  - `create_otp_token()` - Creates OTP with 10-minute expiration
  - `send_verification_email()` - Sends HTML email with OTP via SMTP
  - `verify_otp()` - Validates OTP and checks expiration
  - `is_otp_expired()` - Checks if OTP has expired

#### Updated Models
- `backend/app/models/user.py` - Added fields:
  - `is_email_verified: bool` - Email verification status
  - `otp_code: Optional[str]` - Stored OTP code
  - `otp_expiration: Optional[datetime]` - OTP expiration time

#### Updated Schemas
- `backend/app/schemas/user.py` - Added:
  - `OTPVerification` - Schema for OTP verification request
  - `ResendOTP` - Schema for resend OTP request
  - Updated `UserResponse` to include `is_email_verified`

#### New API Endpoints

**POST `/api/auth/register`**
- Registers user and sends OTP via email
- Returns user data with email not yet verified
- Response includes verification status

**POST `/api/auth/verify-otp`**
- Verifies OTP code
- Requires: Valid JWT token + 6-digit OTP
- Marks email as verified
- Clears OTP from database

**POST `/api/auth/resend-otp`**
- Resends OTP to registered email
- Useful if original OTP expired
- Does not require authentication

**POST `/api/auth/login`**
- Users can login even if email not verified
- Email verification is recommended but optional

### Email Configuration

Environment variables needed:
```
SMTP_SERVER=smtp.gmail.com (default)
SMTP_PORT=587 (default)
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-app-password
```

**Development Mode:**
If `SENDER_EMAIL` or `SENDER_PASSWORD` not set, OTP is logged to console instead of sending email.

### Frontend Implementation

#### New Pages
- `frontend/src/pages/VerifyEmail.jsx` - Email verification page
  - OTP input field (6 digits only)
  - Verify button
  - Resend code option
  - Real-time validation

#### Updated Pages
- `frontend/src/pages/Register.jsx` - Updated to:
  - Redirect to verification page after registration
  - Save email to localStorage for resend functionality
  - Enhanced validation

#### Styles
- `frontend/src/styles/VerifyEmail.css` - Verification page styling

### User Flow
```
1. User fills registration form
   ↓
2. Backend generates OTP and sends email
   ↓
3. User redirected to verification page
   ↓
4. User enters 6-digit code from email
   ↓
5. Backend verifies OTP and marks email as verified
   ↓
6. User can now fully use the platform
   ↓
7. User can resend OTP if code expires
```

---

## 2. TCP Port Scanning

### Features
- **Quick Scan**: Pre-configured scan of 20 common service ports
- **Custom Scan**: Scan specific ports (1-65535)
- **Service Detection**: Identifies common services for open ports
- **Async Scanning**: Non-blocking port scanning
- **Port Limit**: Maximum 100 ports per scan for performance
- **System Verification**: Only scan systems owned by current user

### Backend Implementation

#### New File
- `backend/app/security/port_scanner.py` - Port scanning utilities
  - `scan_port()` - Scans single port asynchronously
  - `scan_ports_async()` - Scans multiple ports concurrently
  - `scan_common_ports()` - Scans 20 common service ports
  - `get_service_name()` - Maps port to service name

#### Scanned Services
Default common ports include:
- FTP (21), SSH (22), Telnet (23), SMTP (25), DNS (53)
- HTTP (80), POP3 (110), IMAP (143), HTTPS (443), SMB (445)
- MySQL (3306), RDP (3389), PostgreSQL (5432), VNC (5900)
- HTTP-Alt (8000), HTTP-Proxy (8080), HTTPS-Alt (8443)
- Elasticsearch (9200), MongoDB (27017), Redis (6379)

#### New API Endpoints

**POST `/api/audits/scan-ports/{system_id}` (Optional query: `custom_ports`)**
- Scans specified ports on a system
- Parameters:
  - `system_id`: ID of registered system
  - `custom_ports`: Optional comma-separated list of ports
- Returns:
  - Scan summary (total, open, closed, errors)
  - Detailed results for each port
  - Open services list

**GET `/api/audits/scan-ports/{system_id}/common`**
- Quick scan of 20 common service ports
- No parameters needed
- Returns same format as custom scan

### Frontend Implementation

#### New Page
- `frontend/src/pages/PortScanning.jsx` - Port scanning interface
  - System selection dropdown
  - Quick scan button (common ports)
  - Custom ports textarea
  - Real-time results display
  - Scan summary with statistics
  - Detailed results table

#### Styles
- `frontend/src/styles/PortScanning.css` - Port scanning page styling
  - Summary boxes (open/closed/error)
  - Results table with service names
  - Responsive design

#### Updated Components
- `frontend/src/components/Sidebar.jsx` - Added Port Scanning menu link
- `frontend/src/App.jsx` - Added port scanning route

### Port Scan Results

Results include for each port:
```json
{
  "port": 80,
  "status": "open|closed|error",
  "service": "HTTP",
  "error": "optional error message"
}
```

### Summary Format
```json
{
  "system_id": "...",
  "hostname": "server-1",
  "ip_address": "192.168.1.100",
  "scan_summary": {
    "total_scanned": 20,
    "open_ports": 3,
    "closed_ports": 16,
    "errors": 1
  },
  "open_services": [...],
  "results": [...]
}
```

### User Flow
```
1. Navigate to Port Scanning page
   ↓
2. Select a registered system
   ↓
3. Choose scan type:
   - Quick Scan (common ports)
   - Custom Scan (specific ports)
   ↓
4. Backend scans ports asynchronously
   ↓
5. Results displayed with:
   - Open ports count
   - Identified services
   - Full results table
   ↓
6. User can export or analyze results
```

---

## Security Considerations

### Email OTP
✓ 6-digit code prevents brute force (1 million combinations)
✓ 10-minute expiration limits window
✓ OTP cleared from DB after verification
✓ Email normalized to lowercase to prevent duplicates
✓ Rate limiting recommended (via middleware)

### Port Scanning
✓ Only system owner can scan their systems
✓ Maximum 100 ports per scan (prevents DoS)
✓ 2-second timeout per port (prevents hanging)
✓ Concurrent scanning using asyncio
✓ Error handling for network issues

---

## Testing Guide

### Email OTP Testing

1. **Development Mode** (no email configured):
   - OTP printed to console
   - Check terminal for code

2. **Production Mode** (with SMTP):
   - Set environment variables
   - Check email inbox for verification code
   - Code expires in 10 minutes

3. **Test Cases**:
   - Invalid OTP → Error message
   - Expired OTP → Resend option
   - Valid OTP → Email verified

### Port Scanning Testing

1. **Quick Scan**:
   ```
   Select system → Click "Scan Common Ports"
   Wait for results → View open services
   ```

2. **Custom Ports**:
   ```
   Enter ports: 80, 443, 8080
   → Results show service status
   ```

3. **Error Handling**:
   - Invalid system ID → Error
   - Network unreachable → Handled gracefully
   - > 100 ports → Error message

---

## Configuration

### Environment Variables (Backend)
```bash
# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-app-password

# Database
MONGODB_URL=mongodb://localhost:27017
DB_NAME=cis_audit

# API
API_HOST=0.0.0.0
API_PORT=8000
```

### Port Scan Configuration
- Default timeout: 2 seconds per port
- Max concurrent connections: Limited by asyncio
- Max ports per request: 100
- Common ports list: Hardcoded in `port_scanner.py`

---

## Future Enhancements

1. **Email OTP**
   - Rate limiting on resend
   - Email confirmation required for registration
   - 2FA (Two-Factor Authentication)

2. **Port Scanning**
   - Service version detection
   - Vulnerability scanning
   - Port scan scheduling
   - Save scan history
   - Export scan reports (PDF, CSV)
   - NMAP integration for advanced scanning

3. **General**
   - Audit logging for both features
   - User activity tracking
   - Email templates customization
   - SMS OTP option

---

## File Structure

```
backend/
├── app/
│   ├── security/
│   │   ├── __init__.py
│   │   ├── port_scanner.py      (NEW)
│   │   ├── email_otp.py         (NEW)
│   ├── api/
│   │   └── auth.py              (UPDATED)
│   │   └── audits.py            (UPDATED)
│   ├── models/
│   │   └── user.py              (UPDATED)
│   ├── schemas/
│   │   └── user.py              (UPDATED)
│
frontend/
├── src/
│   ├── pages/
│   │   ├── VerifyEmail.jsx      (NEW)
│   │   ├── PortScanning.jsx     (NEW)
│   │   ├── Register.jsx         (UPDATED)
│   ├── styles/
│   │   ├── VerifyEmail.css      (NEW)
│   │   ├── PortScanning.css     (NEW)
│   ├── components/
│   │   └── Sidebar.jsx          (UPDATED)
│   └── App.jsx                  (UPDATED)
```

---

## Dependencies

### Backend
- `python-jose[cryptography]` - JWT handling
- `passlib[bcrypt]` - Password hashing
- `email-validator` - Email validation
- `pydantic` - Data validation
- `motor` - Async MongoDB
- `fastapi` - Web framework
- Standard library: `socket`, `asyncio`, `smtplib`

### Frontend
- `react-toastify` - Toast notifications
- `react-router-dom` - Routing

---

## Support & Documentation

For detailed API documentation, visit:
- Backend: `http://localhost:8000/docs` (Swagger UI)
- Backend: `http://localhost:8000/redoc` (ReDoc)
