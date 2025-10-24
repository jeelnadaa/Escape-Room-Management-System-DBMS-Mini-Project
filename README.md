# 🧩 Escape Room Management System (DBMS Mini Project)

A **full-stack web application** for managing and participating in escape rooms.  
Built using **Flask (Python)** for the backend, **MySQL** for the database, and **Tailwind CSS** for a clean, responsive frontend.

---

## 🚀 Overview

The system provides two main roles:

- **👤 Users** can register, log in, browse escape rooms, join upcoming sessions, and play interactive puzzle-based games.
- **🛠️ Admins** can manage rooms, puzzles, hints, and sessions through a dedicated dashboard.

---

## ✨ Features

### 🧑‍💻 User Features
- **🔐 Authentication** – User registration and login system.
- **🏠 Room Browser** – Browse available escape rooms with details such as:
  - Theme  
  - Difficulty  
  - Capacity  
  - Duration  
- **🗓️ Session Registration** – View and register for upcoming sessions.
- **📋 Personal Dashboard** – View all joined sessions (upcoming, active, completed).
- **🎮 Interactive Gameplay**
  - Solve puzzles in sequence during an active session.
  - View hints for each puzzle.
  - Submit answers and get immediate feedback.
  - Track progress — puzzles are marked “Solved” upon a correct answer.

---

### 🧑‍💼 Admin Features
- **🖥️ Admin Panel** – Secure admin dashboard accessible via the main navigation.
- **🏗️ Room Management** – Add new escape rooms (theme, description, difficulty, image).
- **🧩 Puzzle Management** – Create puzzles with specific sequences and correct answers.
- **💡 Hint Management** – Add hints linked to puzzles.
- **🗓️ Session Management** – Schedule new sessions for any room.

---

## 🗃️ Database Features

### 🔁 SQL Triggers
The system uses **MySQL triggers** to automate game logic and activity tracking:

| Trigger Name | Description |
|---------------|--------------|
| `trg_log_session_join` | Logs when a user joins a session. |
| `trg_log_puzzle_attempt` | Logs every puzzle-solving attempt. |
| `trg_check_session_completion` | Marks a session as 'completed' when all puzzles are solved. |

---

## 🛠️ Tech Stack

| Component | Technology |
|------------|-------------|
| **Backend** | Flask (Python) |
| **Database** | MySQL |
| **Connector** | `mysql-connector-python` |
| **Password Security** | Werkzeug (hashing & verification) |
| **Frontend** | HTML + Tailwind CSS |

---

## ⚙️ Getting Started

Follow the steps below to run the project locally.

### 1️⃣ Prerequisites
Make sure you have the following installed:
- [Python 3.x](https://www.python.org/downloads/)
- [MySQL Server](https://dev.mysql.com/downloads/)
- [pip](https://pip.pypa.io/en/stable/)

---

### 2️⃣ Clone the Repository
```bash
git clone https://github.com/jeelnadaa/escape-room-management-system-dbms-mini-project.git
cd escape-room-management-system-dbms-mini-project
```

---

### 3️⃣ Set Up a Virtual Environment
```bash
python -m venv venv

# Activate the virtual environment
# macOS/Linux:
source venv/bin/activate
# Windows:
.venv\Scripts\activate
```

---

### 4️⃣ Install Dependencies
```bash
pip install -r requirments.txt
```

---

### 5️⃣ Database Setup
```sql
CREATE DATABASE escape_room_db;
USE escape_room_db;
```
Run `schema.sql` to create tables, triggers, and insert sample data.

---

### 6️⃣ Configure Database Connection
Edit `DB_CONFIG` in `app.py`:
```python
DB_CONFIG = {
    'user': 'your_mysql_username',
    'password': 'your_mysql_password',
    'host': '127.0.0.1',
    'database': 'escape_room_db',
    'raise_on_warnings': True
}
```

---

### 7️⃣ Run the Application
```bash
python app.py
```
App runs at: **http://127.0.0.1:5001**

---

## 🕹️ How to Use

1. Register new users:
   - Admin → `admin / adminpass`
   - Player → `player / playerpass`
2. Grant admin role manually:
   ```sql
   UPDATE users SET is_admin = 1 WHERE username = 'admin';
   ```
3. Admin → Manage rooms, puzzles, hints, and sessions  
   Player → Join sessions and play puzzles

---

## 🧱 Database Schema Overview

```
users
 ├── id (PK)
 ├── username
 ├── password_hash
 ├── is_admin

rooms
 ├── id (PK)
 ├── name
 ├── theme
 ├── difficulty
 ├── capacity
 ├── duration
 ├── description
 ├── image_url

sessions
 ├── id (PK)
 ├── room_id (FK)
 ├── start_time
 ├── end_time
 ├── status

puzzles
 ├── id (PK)
 ├── room_id (FK)
 ├── sequence_number
 ├── question
 ├── answer

hints
 ├── id (PK)
 ├── puzzle_id (FK)
 ├── hint_text

participants
 ├── id (PK)
 ├── user_id (FK)
 ├── session_id (FK)

puzzle_attempts
 ├── id (PK)
 ├── user_id (FK)
 ├── puzzle_id (FK)
 ├── is_correct

activity_log
 ├── id (PK)
 ├── user_id (FK)
 ├── action
 ├── timestamp
```

---

## 👥 Collaborators
- **Jeel Nada** — *PES2UG23CS357*

---

## 🧠 Future Enhancements
- Leaderboards for top players  
- Timer-based scoring  
- Multiplayer collaboration mode  
- Email verification & password reset  

---

## 🪪 License
This project is for **academic and learning purposes** as part of a **DBMS Mini Project**.
