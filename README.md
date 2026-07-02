# Ticket Generating System with QR Code
**Python · Tkinter · MySQL · QR Code · PDF Export**

---

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure MySQL
Open `database.py` and edit the `DB_CONFIG` block at the top:
```python
DB_CONFIG = {
    "host":     "localhost",
    "port":     3306,
    "user":     "root",           # ← your MySQL username
    "password": "yourpassword",   # ← your MySQL password
    "database": "ticket_system",  # will be created automatically
}
```

### 3. Run the app
```bash
python app.py
```

### 4. Default login
| Username | Password  |
|----------|-----------|
| admin  | admin123 |

> **Change the password immediately** after first login via the 🔒 Change Password page.

---

## Features

| Feature | Description |
|---|---|
| 🔐 Login + password hashing | SHA-256 with random salt per user |
| 🔒 Change password | Verified against current password |
| 📅 Event management | Add / delete events with capacity limits |
| 🎟 Issue tickets | Auto-blocks overbooking |
| 📱 QR code | Unique cryptographic token per ticket |
| 📄 PDF export | Styled ticket with QR, from Issue or All Tickets page |
| 📋 Ticket list | Search by name, email, or ID; cancel / reactivate |

---

## File Structure
```
ticket_system/
├── app.py               # Tkinter GUI (all pages)
├── database.py          # MySQL layer (all queries)
├── ticket_generator.py  # QR image + PDF builder
├── requirements.txt     # pip dependencies
└── README.md
```

---

## MySQL Schema (auto-created)

```sql
users   (id, username, password, salt, role, created_at)
events  (id, title, event_date, event_time, location, capacity, created_at)
tickets (id, event_id→events, buyer_name, buyer_email,
         issued_at, status, qr_token)
```
