use escape_room_db;

-- Drop tables in reverse order of dependencies
DROP TABLE IF EXISTS `puzzle_attempts`;
DROP TABLE IF EXISTS `hints`;
DROP TABLE IF EXISTS `participants`;
DROP TABLE IF EXISTS `activity_log`;
DROP TABLE IF EXISTS `puzzles`;
DROP TABLE IF EXISTS `sessions`;
DROP TABLE IF EXISTS `rooms`;
DROP TABLE IF EXISTS `users`;

-- Table for user authentication
CREATE TABLE users (
  user_id integer PRIMARY KEY AUTO_INCREMENT,
  username varchar(255) UNIQUE NOT NULL,
  password_hash varchar(255) NOT NULL,
  is_admin boolean DEFAULT 0
);

-- Table for escape rooms
CREATE TABLE rooms (
  room_id integer PRIMARY KEY AUTO_INCREMENT,
  theme varchar(255) NOT NULL,
  difficulty varchar(255),
  capacity integer,
  duration integer,
  description text,
  image_url varchar(255)
);

-- Table for puzzles within rooms
CREATE TABLE puzzles (
  puzzle_id integer PRIMARY KEY AUTO_INCREMENT,
  room_id integer NOT NULL,
  description text,
  type varchar(255),
  sequence_number integer,
  answer varchar(255) NOT NULL, -- Added to check correct answers
  FOREIGN KEY (room_id) REFERENCES rooms (room_id) ON DELETE CASCADE
);

-- Table for game sessions
CREATE TABLE sessions (
  session_id integer PRIMARY KEY AUTO_INCREMENT,
  room_id integer NOT NULL,
  date_time timestamp NOT NULL,
  status ENUM('upcoming', 'active', 'completed') DEFAULT 'upcoming',
  FOREIGN KEY (room_id) REFERENCES rooms (room_id) ON DELETE CASCADE
);

-- Table to link users (participants) to sessions
CREATE TABLE participants (
  participant_id integer PRIMARY KEY AUTO_INCREMENT,
  user_id integer NOT NULL,
  session_id integer NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
  FOREIGN KEY (session_id) REFERENCES sessions (session_id) ON DELETE CASCADE,
  UNIQUE(user_id, session_id) -- A user can only join the same session once
);

-- Table for hints
CREATE TABLE hints (
  hint_id integer PRIMARY KEY AUTO_INCREMENT,
  puzzle_id integer NOT NULL,
  hint_text text,
  FOREIGN KEY (puzzle_id) REFERENCES puzzles (puzzle_id) ON DELETE CASCADE
);

-- Table to log puzzle attempts
CREATE TABLE puzzle_attempts (
  attempt_id integer PRIMARY KEY AUTO_INCREMENT,
  session_id integer NOT NULL,
  puzzle_id integer NOT NULL,
  user_id integer NOT NULL, -- Added to log *who* made the attempt
  attempt_time timestamp DEFAULT CURRENT_TIMESTAMP,
  submitted_answer text,
  is_solved boolean DEFAULT 0,
  FOREIGN KEY (session_id) REFERENCES sessions (session_id) ON DELETE CASCADE,
  FOREIGN KEY (puzzle_id) REFERENCES puzzles (puzzle_id) ON DELETE CASCADE,
  FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
);

-- Table for logging user actions (for Triggers 2 & 3)
CREATE TABLE activity_log (
  log_id integer PRIMARY KEY AUTO_INCREMENT,
  user_id integer,
  session_id integer,
  action varchar(255),
  log_time timestamp DEFAULT CURRENT_TIMESTAMP
);

-- -------------------
-- --- TRIGGERS ---
-- -------------------

DELIMITER $$

-- TRIGGER 1: If all puzzles are solved, mark the session 'completed'
-- This trigger fires after a new (and correct) puzzle attempt is logged.
CREATE TRIGGER trg_check_session_completion
AFTER INSERT ON puzzle_attempts
FOR EACH ROW
BEGIN
    DECLARE solved_count INT;
    DECLARE total_puzzles INT;
    DECLARE v_room_id INT;

    -- Only run this logic if the new attempt was successful
    IF NEW.is_solved = 1 THEN
        -- Get the room_id for this session
        SELECT room_id INTO v_room_id FROM sessions WHERE session_id = NEW.session_id;

        -- Count total puzzles for this room
        SELECT COUNT(*) INTO total_puzzles FROM puzzles WHERE room_id = v_room_id;

        -- Count unique solved puzzles for this session
        SELECT COUNT(DISTINCT puzzle_id) INTO solved_count
        FROM puzzle_attempts
        WHERE session_id = NEW.session_id AND is_solved = 1;

        -- If counts match, update the session status
        IF solved_count = total_puzzles THEN
            UPDATE sessions SET status = 'completed' WHERE session_id = NEW.session_id;
        END IF;
    END IF;
END$$

-- TRIGGER 2: If a user joins a session, log it
-- This trigger fires after a user is added to the 'participants' table.
CREATE TRIGGER trg_log_session_join
AFTER INSERT ON participants
FOR EACH ROW
BEGIN
    INSERT INTO activity_log (user_id, session_id, action)
    VALUES (NEW.user_id, NEW.session_id, 'SESSION_JOIN');
END$$

-- TRIGGER 3: If a user attempts a puzzle, log it
-- This trigger fires after an attempt is added to the 'puzzle_attempts' table.
CREATE TRIGGER trg_log_puzzle_attempt
AFTER INSERT ON puzzle_attempts
FOR EACH ROW
BEGIN
    INSERT INTO activity_log (user_id, session_id, action)
    VALUES (NEW.user_id, NEW.session_id, 'PUZZLE_ATTEMPT');
END$$

DELIMITER ;

-- ---------------------
-- --- SAMPLE DATA ---
-- ---------------------

-- Admin and a regular user
INSERT INTO users (username, password_hash, is_admin) VALUES
('admin', 'pbkdf2:sha256:600000$NAaV4aG1t9XzKqKq$c8b77d6c56f7161b9a92a54b38d3cea8e65f33f00a563914b1a415501815b881', 1), -- password: admin
('user', 'pbkdf2:sha256:600000$gS5VqA8Jt8YxJtYp$69EA0bLDvbM8jyxT6lBLgp3M1d99/B2PInpafhGqvbY', 0); -- password: user

-- Rooms
INSERT INTO rooms (theme, difficulty, capacity, duration, description, image_url) VALUES
('Pharaoh''s Curse', 'Hard', 6, 60, 'Escape the ancient tomb before you are trapped forever.', 'https://placehold.co/600x400/f4a261/ffffff?text=Pharaohs+Curse'),
('Space Odyssey', 'Medium', 8, 45, 'Repair your spaceship and escape the black hole!', 'https://placehold.co/600x400/2a9d8f/ffffff?text=Space+Odyssey');

-- Sessions
INSERT INTO sessions (room_id, date_time, status) VALUES
(1, '2025-10-30 18:00:00', 'upcoming'),
(1, '2025-10-30 20:00:00', 'upcoming'),
(2, '2025-11-01 19:00:00', 'upcoming');

-- Puzzles
INSERT INTO puzzles (room_id, description, type, sequence_number, answer) VALUES
(1, 'What has a mouth, but never speaks, and a bed, but never sleeps?', 'Riddle', 1, 'river'),
(1, 'I have cities, but no houses, and mountains, but no trees. I have water, but no fish. What am I?', 'Riddle', 2, 'map'),
(2, 'What planet is known as the Red Planet?', 'Trivia', 1, 'Mars'),
(2, 'What force keeps planets in orbit around the sun?', 'Trivia', 2, 'gravity');

-- Hints
INSERT INTO hints (puzzle_id, hint_text) VALUES
(1, 'It flows.'),
(1, 'You can find it in a valley.'),
(2, 'Look at your wall.'),
(3, 'It is the fourth planet from the sun.'),
(4, 'It''s what keeps you on the ground.');

-- Make 'jeel' an admin user
UPDATE users SET is_admin = 1 WHERE username = 'jeel';
