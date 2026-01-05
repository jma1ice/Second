import sqlite3, os, hashlib, random, string
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime

app = Flask(__name__)

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS polls (
            id TEXT PRIMARY KEY,
            topic TEXT NOT NULL,
            option1 TEXT NOT NULL,
            option2 TEXT NOT NULL,
            option3 TEXT NOT NULL,
            creator_ip TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_closed INTEGER DEFAULT 0
        );
        
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            poll_id TEXT,
            option_choice INTEGER,
            voter_ip TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (poll_id) REFERENCES polls (id),
            UNIQUE(poll_id, voter_ip)
        );
    ''')
    conn.commit()
    conn.close()

def generate_poll_id():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))

def get_client_ip():
    return request.environ.get('HTTP_X_FORWARDED_FOR') or request.environ.get('REMOTE_ADDR')

@app.route('/')
def home():
    conn = get_db()
    polls = conn.execute('''
        SELECT id, topic, created_at, is_closed,
               (SELECT COUNT(*) FROM votes WHERE poll_id = polls.id) as vote_count
        FROM polls 
        ORDER BY created_at DESC 
        LIMIT 10
    ''').fetchall()
    conn.close()
    return render_template('home.html', polls=polls)

@app.route('/create', methods=['GET', 'POST'])
def create_poll():
    if request.method == 'POST':
        topic = request.form.get('topic', '').strip()
        option1 = request.form.get('option1', '').strip()
        option2 = request.form.get('option2', '').strip()
        option3 = request.form.get('option3', '').strip()
        
        if not all([topic, option1, option2, option3]):
            flash('All fields are required!', 'error')
            return render_template('create.html')
        
        poll_id = generate_poll_id()
        
        conn = get_db()
        while conn.execute('SELECT id FROM polls WHERE id = ?', (poll_id,)).fetchone():
            poll_id = generate_poll_id()
        
        conn.execute('''
            INSERT INTO polls (id, topic, option1, option2, option3, creator_ip)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (poll_id, topic, option1, option2, option3, get_client_ip()))
        conn.commit()
        conn.close()
        
        flash(f'Poll created! Share this link: /poll/{poll_id}', 'success')
        return redirect(url_for('view_poll', poll_id=poll_id))
    
    return render_template('create.html')

@app.route('/poll/<poll_id>')
def view_poll(poll_id):
    conn = get_db()
    poll = conn.execute('SELECT * FROM polls WHERE id = ?', (poll_id,)).fetchone()
    
    if not poll:
        flash('Poll not found!', 'error')
        return redirect(url_for('home'))
    
    has_voted = conn.execute(
        'SELECT 1 FROM votes WHERE poll_id = ? AND voter_ip = ?',
        (poll_id, get_client_ip())
    ).fetchone()
    
    vote_counts = {}
    votes = conn.execute(
        'SELECT option_choice, COUNT(*) as count FROM votes WHERE poll_id = ? GROUP BY option_choice',
        (poll_id,)
    ).fetchall()
    
    for vote in votes:
        vote_counts[vote['option_choice']] = vote['count']
    
    total_votes = sum(vote_counts.values())
    conn.close()
    
    return render_template('poll.html', 
                         poll=poll, 
                         has_voted=has_voted, 
                         vote_counts=vote_counts,
                         total_votes=total_votes)

@app.route('/vote/<poll_id>', methods=['POST'])
def vote(poll_id):
    option_choice = request.form.get('option')
    
    if not option_choice or option_choice not in ['1', '2', '3']:
        flash('Invalid vote!', 'error')
        return redirect(url_for('view_poll', poll_id=poll_id))
    
    conn = get_db()
    poll = conn.execute('SELECT * FROM polls WHERE id = ?', (poll_id,)).fetchone()
    
    if not poll:
        flash('Poll not found!', 'error')
        return redirect(url_for('home'))
    
    if poll['is_closed']:
        flash('This poll is closed!', 'error')
        return redirect(url_for('view_poll', poll_id=poll_id))
    
    try:
        conn.execute('''
            INSERT INTO votes (poll_id, option_choice, voter_ip)
            VALUES (?, ?, ?)
        ''', (poll_id, int(option_choice), get_client_ip()))
        conn.commit()
        flash('Vote submitted!', 'success')
    except sqlite3.IntegrityError:
        flash('You have already voted on this poll!', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('view_poll', poll_id=poll_id))

@app.route('/poll/<poll_id>/results')
def results(poll_id):
    conn = get_db()
    poll = conn.execute('SELECT * FROM polls WHERE id = ?', (poll_id,)).fetchone()
    
    if not poll:
        flash('Poll not found!', 'error')
        return redirect(url_for('home'))
    
    vote_counts = {1: 0, 2: 0, 3: 0}
    votes = conn.execute(
        'SELECT option_choice, COUNT(*) as count FROM votes WHERE poll_id = ? GROUP BY option_choice',
        (poll_id,)
    ).fetchall()
    
    for vote in votes:
        vote_counts[vote['option_choice']] = vote['count']
    
    sorted_results = sorted(vote_counts.items(), key=lambda x: x[1], reverse=True)
    
    winner_option = None
    winner_text = "No votes yet"
    
    if sorted_results[0][1] > 0:
        if len(sorted_results) >= 2 and sorted_results[1][1] > 0:
            winner_option = sorted_results[1][0]
            option_name = ['', poll['option1'], poll['option2'], poll['option3']][winner_option]
            winner_text = f"'{option_name}' (2nd place with {sorted_results[1][1]} votes)"
        else:
            winner_text = "Only one option received votes"
    
    conn.close()
    
    return render_template('results.html', 
                         poll=poll, 
                         vote_counts=vote_counts,
                         sorted_results=sorted_results,
                         winner_option=winner_option,
                         winner_text=winner_text)

@app.route('/poll/<poll_id>/close', methods=['POST'])
def close_poll(poll_id):
    conn = get_db()
    poll = conn.execute('SELECT * FROM polls WHERE id = ?', (poll_id,)).fetchone()
    
    if not poll:
        flash('Poll not found!', 'error')
        return redirect(url_for('home'))
    
    if poll['creator_ip'] != get_client_ip():
        flash('Only the poll creator can close this poll!', 'error')
        return redirect(url_for('view_poll', poll_id=poll_id))
    
    conn.execute('UPDATE polls SET is_closed = 1 WHERE id = ?', (poll_id,))
    conn.commit()
    conn.close()
    
    flash('Poll closed!', 'success')
    return redirect(url_for('results', poll_id=poll_id))

if __name__ == '__main__':
    app.secret_key = 'your-secret-key-change-this'
    DATABASE = 'second_game.db'
    init_db()
    app.run(debug=True, host='0.0.0.0', port=22222)