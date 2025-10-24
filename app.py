import mysql.connector
from mysql.connector import errorcode
from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import datetime

app = Flask(__name__)
app.secret_key = b'b\x8a\x07\x1f\x98\x12\x1a\x89\x0b\xd6\x0c\xd0\x9e\x9c\x07\x92\x95\x0c\x13\x11\xa2\x94\xf4\x8e'

# --- !! IMPORTANT !! ---
# --- DATABASE CONFIGURATION ---
# --- Edit this with your MySQL details ---
DB_CONFIG = {
    'user': 'username of the database',
    'password': 'password of the database',
    'host': '127.0.0.1', # or your database host
    'database': 'name of the database',
    'raise_on_warnings': True
}

# --- Database Connection Handling ---

def get_db():
    """Get a database connection for the current request."""
    if 'db' not in g:
        try:
            g.db = mysql.connector.connect(**DB_CONFIG)
            g.cursor = g.db.cursor(dictionary=True) # Use dictionary cursor
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                flash("Error: Something is wrong with your user name or password", "danger")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                flash("Error: Database does not exist", "danger")
            else:
                flash(f"Error: {err}", "danger")
            return None, None
    return g.db, g.cursor

@app.teardown_appcontext
def close_db(e=None):
    """Close the database connection at the end of the request."""
    cursor = g.pop('cursor', None)
    if cursor is not None:
        cursor.close()
    db = g.pop('db', None)
    if db is not None:
        db.close()

# --- Authentication Decorators ---

def login_required(f):
    """Decorator to require login for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("You must be logged in to view this page.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin privileges for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("You must be logged in to view this page.", "warning")
            return redirect(url_for('login'))
        if not session.get('is_admin'):
            flash("You do not have permission to access this page.", "danger")
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# --- Authentication Routes ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login and registration."""
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        db, cursor = get_db()
        if not db:
            return render_template('login.html')

        username = request.form['username']
        password = request.form['password']
        action = request.form['action']

        # Check if user exists
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()

        if action == 'register':
            if user:
                flash("Username already exists.", "danger")
            elif not username or not password:
                flash("Username and password are required.", "warning")
            else:
                # Create new user
                password_hash = generate_password_hash(password)
                try:
                    cursor.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)",
                                   (username, password_hash))
                    db.commit()
                    flash("Registration successful! Please log in.", "success")
                except mysql.connector.Error as err:
                    flash(f"Database error: {err}", "danger")
                return redirect(url_for('login'))
        
        elif action == 'login':
            if user and check_password_hash(user['password_hash'], password):
                # Log user in
                session['user_id'] = user['user_id']
                session['username'] = user['username']
                session['is_admin'] = user['is_admin']
                flash("Logged in successfully!", "success")
                return redirect(url_for('index'))
            else:
                flash("Invalid username or password.", "danger")

    return render_template('login.html')

@app.route('/logout')
def logout():
    """Log the user out."""
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

# --- User Routes ---

@app.route('/')
@login_required
def index():
    """Show all available escape rooms."""
    db, cursor = get_db()
    if not db:
        return redirect(url_for('login'))
        
    cursor.execute("SELECT * FROM rooms ORDER BY theme")
    rooms = cursor.fetchall()
    
    # Get user's registered sessions
    cursor.execute("""
        SELECT s.session_id, s.date_time, s.status, r.theme
        FROM sessions s
        JOIN participants p ON s.session_id = p.session_id
        JOIN rooms r ON s.room_id = r.room_id
        WHERE p.user_id = %s
        ORDER BY s.date_time DESC
    """, (session['user_id'],))
    my_sessions = cursor.fetchall()
    
    return render_template('index.html', rooms=rooms, my_sessions=my_sessions)

@app.route('/room/<int:room_id>')
@login_required
def room_details(room_id):
    """Show details for a single room and its upcoming sessions."""
    db, cursor = get_db()
    if not db:
        return redirect(url_for('index'))

    # Get room details
    cursor.execute("SELECT * FROM rooms WHERE room_id = %s", (room_id,))
    room = cursor.fetchone()
    if not room:
        flash("Room not found.", "danger")
        return redirect(url_for('index'))

    # Get upcoming sessions for this room
    cursor.execute("""
        SELECT * FROM sessions 
        WHERE room_id = %s AND status = 'upcoming' AND date_time > NOW()
        ORDER BY date_time
    """, (room_id,))
    sessions_list = cursor.fetchall()

    return render_template('room.html', room=room, sessions=sessions_list)

@app.route('/register_session', methods=['POST'])
@login_required
def register_session():
    """Register the current user for a session."""
    db, cursor = get_db()
    if not db:
        return redirect(url_for('index'))

    session_id = request.form['session_id']
    user_id = session['user_id']

    try:
        # The trg_log_session_join trigger will fire on this insert
        cursor.execute("INSERT INTO participants (user_id, session_id) VALUES (%s, %s)",
                       (user_id, session_id))
        db.commit()
        flash("Successfully registered for the session!", "success")
    except mysql.connector.Error as err:
        if err.errno == 1062: # Duplicate entry
             flash("You are already registered for this session.", "warning")
        else:
             flash(f"Database error: {err}", "danger")

    return redirect(url_for('index'))

@app.route('/session/<int:session_id>')
@login_required
def play_session(session_id):
    """The main "play" page for a session."""
    db, cursor = get_db()
    if not db:
        return redirect(url_for('index'))

    # 1. Verify user is a participant
    cursor.execute("SELECT * FROM participants WHERE user_id = %s AND session_id = %s",
                   (session['user_id'], session_id))
    participant = cursor.fetchone()
    if not participant:
        flash("You are not registered for this session.", "danger")
        return redirect(url_for('index'))

    # 2. Get session and room details
    cursor.execute("""
        SELECT s.*, r.theme, r.room_id
        FROM sessions s
        JOIN rooms r ON s.room_id = r.room_id
        WHERE s.session_id = %s
    """, (session_id,))
    session_details = cursor.fetchone()

    # 3. If session is completed, redirect
    if session_details['status'] == 'completed':
        flash("This session is already completed. Well done!", "success")
        return redirect(url_for('index'))

    # 4. Get all puzzles for the room
    cursor.execute("SELECT * FROM puzzles WHERE room_id = %s ORDER BY sequence_number",
                   (session_details['room_id'],))
    puzzles = cursor.fetchall()

    # 5. Get all hints for those puzzles
    puzzle_ids = [p['puzzle_id'] for p in puzzles]
    if puzzle_ids:
        # Using FORMAT() to create the correct number of %s placeholders
        hint_query = "SELECT * FROM hints WHERE puzzle_id IN ({})".format(','.join(['%s'] * len(puzzle_ids)))
        cursor.execute(hint_query, tuple(puzzle_ids))
        hints = cursor.fetchall()
        
        # Attach hints to their puzzles
        for p in puzzles:
            p['hints'] = [h for h in hints if h['puzzle_id'] == p['puzzle_id']]
    
    # 6. Get solved puzzle IDs for this session
    cursor.execute("""
        SELECT DISTINCT puzzle_id FROM puzzle_attempts
        WHERE session_id = %s AND is_solved = 1
    """, (session_id,))
    solved_puzzles_list = cursor.fetchall()
    solved_puzzle_ids = {sp['puzzle_id'] for sp in solved_puzzles_list}

    return render_template('session.html', 
                           session=session_details, 
                           puzzles=puzzles, 
                           solved_puzzle_ids=solved_puzzle_ids)

@app.route('/session/submit_answer', methods=['POST'])
@login_required
def submit_answer():
    """Check a puzzle answer and log the attempt."""
    db, cursor = get_db()
    if not db:
        return redirect(url_for('index'))

    session_id = request.form['session_id']
    puzzle_id = request.form['puzzle_id']
    submitted_answer = request.form['answer']
    user_id = session['user_id']

    # Check if answer is correct
    cursor.execute("SELECT answer FROM puzzles WHERE puzzle_id = %s", (puzzle_id,))
    puzzle = cursor.fetchone()

    is_solved = 0
    if puzzle and puzzle['answer'].lower() == submitted_answer.lower():
        is_solved = 1
        flash("Correct! The puzzle is solved.", "success")
    else:
        flash("Incorrect. Try again!", "danger")

    # Log the attempt.
    # This will fire BOTH trg_log_puzzle_attempt AND trg_check_session_completion
    try:
        cursor.execute("""
            INSERT INTO puzzle_attempts (session_id, puzzle_id, user_id, submitted_answer, is_solved)
            VALUES (%s, %s, %s, %s, %s)
        """, (session_id, puzzle_id, user_id, submitted_answer, is_solved))
        db.commit()
    except mysql.connector.Error as err:
        flash(f"Error logging attempt: {err}", "danger")

    return redirect(url_for('play_session', session_id=session_id))


# --- Admin Routes ---

@app.route('/admin')
@admin_required
def admin_dashboard():
    """Admin page to add new rooms, sessions, puzzles, and hints."""
    db, cursor = get_db()
    if not db:
        return redirect(url_for('index'))
        
    cursor.execute("SELECT room_id, theme FROM rooms ORDER BY theme")
    rooms = cursor.fetchall()
    
    cursor.execute("""
        SELECT p.puzzle_id, p.description, r.theme
        FROM puzzles p
        JOIN rooms r ON p.room_id = r.room_id
        ORDER BY r.theme, p.sequence_number
    """)
    puzzles = cursor.fetchall()

    return render_template('admin.html', rooms=rooms, puzzles=puzzles)

@app.route('/admin/add_room', methods=['POST'])
@admin_required
def add_room():
    db, cursor = get_db()
    if not db:
        return redirect(url_for('admin_dashboard'))
    try:
        form = request.form

        image_url = form['image_url']
        theme = form['theme'].replace(" ", "+")
        if not image_url:
            image_url = f'https://placehold.co/600x400/cccccc/ffffff?text={theme}'

        cursor.execute("""
            INSERT INTO rooms (theme, difficulty, capacity, duration, description, image_url)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (form['theme'], form['difficulty'], form['capacity'], form['duration'], form['description'], image_url))
        db.commit()
        flash("Room added successfully.", "success")
    except mysql.connector.Error as err:
        flash(f"Database error: {err}", "danger")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/add_session', methods=['POST'])
@admin_required
def add_session():
    db, cursor = get_db()
    if not db:
        return redirect(url_for('admin_dashboard'))
    try:
        form = request.form
        # Convert HTML datetime-local string to MySQL timestamp format
        date_time = datetime.datetime.fromisoformat(form['date_time']).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("INSERT INTO sessions (room_id, date_time) VALUES (%s, %s)",
                       (form['room_id'], date_time))
        db.commit()
        flash("Session added successfully.", "success")
    except mysql.connector.Error as err:
        flash(f"Database error: {err}", "danger")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/add_puzzle', methods=['POST'])
@admin_required
def add_puzzle():
    db, cursor = get_db()
    if not db:
        return redirect(url_for('admin_dashboard'))
    try:
        form = request.form
        cursor.execute("""
            INSERT INTO puzzles (room_id, description, type, sequence_number, answer)
            VALUES (%s, %s, %s, %s, %s)
        """, (form['room_id'], form['description'], form['type'], form['sequence_number'], form['answer']))
        db.commit()
        flash("Puzzle added successfully.", "success")
    except mysql.connector.Error as err:
        flash(f"Database error: {err}", "danger")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/add_hint', methods=['POST'])
@admin_required
def add_hint():
    db, cursor = get_db()
    if not db:
        return redirect(url_for('admin_dashboard'))
    try:
        form = request.form
        cursor.execute("INSERT INTO hints (puzzle_id, hint_text) VALUES (%s, %s)",
                       (form['puzzle_id'], form['hint_text']))
        db.commit()
        flash("Hint added successfully.", "success")
    except mysql.connector.Error as err:
        flash(f"Database error: {err}", "danger")
    return redirect(url_for('admin_dashboard'))

# --- Main ---
if __name__ == '__main__':
    app.run(debug=True, port=5001)

