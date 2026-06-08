from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room
import random
import threading
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'quiz-secret-key-2026'
socketio = SocketIO(
    app,
    cors_allowed_origins="*"
)

rooms = {}

# Answers stay on the backend only. The frontend only receives id/question/options.
GAME_QUESTION_COUNT = 10

QUESTIONS = [
    {'id': 1, 'question': 'Which player has won the most Ballon d\'Or awards?', 'options': ['Cristiano Ronaldo', 'Lionel Messi', 'Zinedine Zidane', 'Ronaldo Nazario'], 'correct': 1},
    {'id': 2, 'question': 'Which country won the 2022 FIFA World Cup?', 'options': ['France', 'Brazil', 'Argentina', 'Germany'], 'correct': 2},
    {'id': 3, 'question': 'Which club is known as The Red Devils?', 'options': ['Liverpool', 'Manchester United', 'Arsenal', 'AC Milan'], 'correct': 1},
    {'id': 4, 'question': 'Who scored the famous Aguero 93:20 goal?', 'options': ['Carlos Tevez', 'David Silva', 'Sergio Aguero', 'Yaya Toure'], 'correct': 2},
    {'id': 5, 'question': 'Which country does Erling Haaland represent?', 'options': ['Sweden', 'Norway', 'Denmark', 'Germany'], 'correct': 1},
    {'id': 6, 'question': 'Which team won the Premier League in 2015/16?', 'options': ['Chelsea', 'Manchester City', 'Leicester City', 'Arsenal'], 'correct': 2},
    {'id': 7, 'question': 'Which stadium is home to Real Madrid?', 'options': ['Camp Nou', 'San Siro', 'Santiago Bernabeu', 'Anfield'], 'correct': 2},
    {'id': 8, 'question': 'Who is Arsenal\'s all-time top goalscorer?', 'options': ['Dennis Bergkamp', 'Thierry Henry', 'Ian Wright', 'Robin van Persie'], 'correct': 1},
    {'id': 9, 'question': 'Which club did Mohamed Salah join Liverpool from?', 'options': ['Roma', 'Chelsea', 'Basel', 'Fiorentina'], 'correct': 0},
    {'id': 10, 'question': 'Which nation won Euro 2016?', 'options': ['France', 'Portugal', 'Spain', 'Italy'], 'correct': 1},
    {'id': 11, 'question': 'Who scored the winning goal for Spain in the 2010 FIFA World Cup final?', 'options': ['Xavi', 'Andres Iniesta', 'David Villa', 'Fernando Torres'], 'correct': 1},
    {'id': 12, 'question': 'Which club won the first Premier League title in 1992/93?', 'options': ['Manchester United', 'Blackburn Rovers', 'Arsenal', 'Leeds United'], 'correct': 0},
    {'id': 13, 'question': 'Which goalkeeper has the most Premier League clean sheets?', 'options': ['David Seaman', 'Petr Cech', 'Edwin van der Sar', 'Peter Schmeichel'], 'correct': 1},
    {'id': 14, 'question': 'Which manager led Porto to the 2003/04 UEFA Champions League title?', 'options': ['Jose Mourinho', 'Andre Villas-Boas', 'Bobby Robson', 'Luigi Delneri'], 'correct': 0},
    {'id': 15, 'question': 'Which player scored Liverpool\'s opening goal in the 2005 Champions League final comeback?', 'options': ['Steven Gerrard', 'Xabi Alonso', 'Vladimir Smicer', 'Luis Garcia'], 'correct': 0},
    {'id': 16, 'question': 'Which club did Robert Lewandowski play for before joining Bayern Munich?', 'options': ['Lech Poznan', 'Borussia Dortmund', 'Legia Warsaw', 'Wolfsburg'], 'correct': 1},
    {'id': 17, 'question': 'Which country knocked Brazil out of the 2006 FIFA World Cup?', 'options': ['Italy', 'France', 'Germany', 'Netherlands'], 'correct': 1},
    {'id': 18, 'question': 'Who won the Golden Boot at the 2018 FIFA World Cup?', 'options': ['Kylian Mbappe', 'Romelu Lukaku', 'Harry Kane', 'Antoine Griezmann'], 'correct': 2},
    {'id': 19, 'question': 'Which club is nicknamed The Old Lady?', 'options': ['Juventus', 'AC Milan', 'Inter Milan', 'Roma'], 'correct': 0},
    {'id': 20, 'question': 'Who scored the Hand of God goal in the 1986 FIFA World Cup?', 'options': ['Pele', 'Diego Maradona', 'Michel Platini', 'Johan Cruyff'], 'correct': 1},
    {'id': 21, 'question': 'Which team won the UEFA Champions League in 2011/12?', 'options': ['Bayern Munich', 'Chelsea', 'Barcelona', 'Real Madrid'], 'correct': 1},
    {'id': 22, 'question': 'Which nation won the first FIFA World Cup in 1930?', 'options': ['Brazil', 'Argentina', 'Uruguay', 'Italy'], 'correct': 2},
    {'id': 23, 'question': 'Which player is known as Il Fenomeno?', 'options': ['Ronaldinho', 'Ronaldo Nazario', 'Romario', 'Kaka'], 'correct': 1},
    {'id': 24, 'question': 'Which club won the treble under Pep Guardiola in 2008/09?', 'options': ['Barcelona', 'Bayern Munich', 'Manchester City', 'Inter Milan'], 'correct': 0},
    {'id': 25, 'question': 'Who scored the decisive penalty for Italy in the 2006 World Cup final shootout?', 'options': ['Andrea Pirlo', 'Fabio Grosso', 'Francesco Totti', 'Alessandro Del Piero'], 'correct': 1},
    {'id': 26, 'question': 'Which club did Luka Modric join Real Madrid from?', 'options': ['Dinamo Zagreb', 'Inter Milan', 'Tottenham Hotspur', 'Sevilla'], 'correct': 2},
    {'id': 27, 'question': 'Which African nation reached the 2022 FIFA World Cup semi-finals?', 'options': ['Senegal', 'Morocco', 'Ghana', 'Cameroon'], 'correct': 1},
    {'id': 28, 'question': 'Who managed Arsenal during their Invincibles Premier League season?', 'options': ['George Graham', 'Arsene Wenger', 'Unai Emery', 'Bruce Rioch'], 'correct': 1},
    {'id': 29, 'question': 'Which player scored a hat-trick for Manchester United against Bayern Munich in the 1998/99 Champions League final?', 'options': ['Dwight Yorke', 'Andy Cole', 'Teddy Sheringham', 'No player scored a hat-trick'], 'correct': 3},
    {'id': 30, 'question': 'Which team did Greece beat in the Euro 2004 final?', 'options': ['Portugal', 'Czech Republic', 'France', 'Netherlands'], 'correct': 0},
    {'id': 31, 'question': 'Which club did Karim Benzema join after leaving Real Madrid in 2023?', 'options': ['Al Hilal', 'Al Nassr', 'Al Ittihad', 'Al Ahli'], 'correct': 2},
    {'id': 32, 'question': 'Who scored the fastest goal in Premier League history?', 'options': ['Ledley King', 'Shane Long', 'Alan Shearer', 'Sadio Mane'], 'correct': 1},
    {'id': 33, 'question': 'Which country hosted the 1998 FIFA World Cup?', 'options': ['Germany', 'France', 'USA', 'South Korea and Japan'], 'correct': 1},
    {'id': 34, 'question': 'Which player won the Ballon d\'Or in 2007?', 'options': ['Cristiano Ronaldo', 'Kaka', 'Lionel Messi', 'Ronaldinho'], 'correct': 1},
    {'id': 35, 'question': 'Which English club did N\'Golo Kante join first?', 'options': ['Chelsea', 'Leicester City', 'Arsenal', 'West Ham United'], 'correct': 1},
    {'id': 36, 'question': 'Which club won Serie A in 2022/23?', 'options': ['AC Milan', 'Inter Milan', 'Napoli', 'Juventus'], 'correct': 2},
    {'id': 37, 'question': 'Which player scored the winning goal in the Euro 2016 final?', 'options': ['Cristiano Ronaldo', 'Eder', 'Nani', 'Ricardo Quaresma'], 'correct': 1},
    {'id': 38, 'question': 'Which stadium hosted the 2012 Olympic football final?', 'options': ['Wembley Stadium', 'Old Trafford', 'Millennium Stadium', 'Emirates Stadium'], 'correct': 0},
    {'id': 39, 'question': 'Which club did Luis Suarez join immediately after leaving Liverpool?', 'options': ['Atletico Madrid', 'Barcelona', 'Ajax', 'Inter Miami'], 'correct': 1},
    {'id': 40, 'question': 'Which nation did England beat in the Euro 2020 semi-final?', 'options': ['Germany', 'Ukraine', 'Denmark', 'Croatia'], 'correct': 2},
    {'id': 41, 'question': 'Which club won the UEFA Champions League in 2018/19?', 'options': ['Liverpool', 'Tottenham Hotspur', 'Real Madrid', 'Ajax'], 'correct': 0},
    {'id': 42, 'question': 'Who was Manchester City\'s manager when they won their first Premier League title?', 'options': ['Manuel Pellegrini', 'Roberto Mancini', 'Pep Guardiola', 'Mark Hughes'], 'correct': 1},
    {'id': 43, 'question': 'Which country did Zinedine Zidane score twice against in the 1998 World Cup final?', 'options': ['Brazil', 'Italy', 'Croatia', 'Germany'], 'correct': 0},
    {'id': 44, 'question': 'Which club did Eden Hazard join Real Madrid from?', 'options': ['Lille', 'Chelsea', 'Borussia Dortmund', 'Monaco'], 'correct': 1},
    {'id': 45, 'question': 'Which team won the 2020/21 UEFA Champions League?', 'options': ['Manchester City', 'Chelsea', 'Bayern Munich', 'Paris Saint-Germain'], 'correct': 1},
    {'id': 46, 'question': 'Who is the only goalkeeper to have won the Ballon d\'Or?', 'options': ['Lev Yashin', 'Gianluigi Buffon', 'Manuel Neuer', 'Iker Casillas'], 'correct': 0},
    {'id': 47, 'question': 'Which club did Jude Bellingham join Real Madrid from?', 'options': ['Birmingham City', 'Borussia Dortmund', 'Bayern Munich', 'RB Leipzig'], 'correct': 1},
    {'id': 48, 'question': 'Which nation won the 2019 Copa America?', 'options': ['Argentina', 'Brazil', 'Chile', 'Uruguay'], 'correct': 1},
    {'id': 49, 'question': 'Who scored Real Madrid\'s goal in the 2021/22 Champions League final?', 'options': ['Karim Benzema', 'Vinicius Junior', 'Luka Modric', 'Rodrygo'], 'correct': 1},
    {'id': 50, 'question': 'Which country won the 2010 Africa Cup of Nations?', 'options': ['Ghana', 'Ivory Coast', 'Egypt', 'Nigeria'], 'correct': 2},
]



class GameRoom:
    """Manages one 2-player quiz room."""

    def __init__(self, room_code):
        """Create an empty room with default game state."""
        self.room_code = room_code
        self.players = {}
        self.current_question_index = 0
        self.selected_questions = []
        self.game_started = False
        self.game_ended = False
        self.question_timeout = None
        self.is_evaluating = False

    def add_player(self, player_id, player_name):
        """Add a player if the room is not full and the game has not started."""
        if len(self.players) >= 2 or self.game_started:
            return False

        self.players[player_id] = {
            'id': player_id,
            'name': player_name,
            'score': 0,
            'current_answer': None,
            'answers': [],
            'is_ready': False,
        }
        return True

    def remove_player(self, player_id):
        """Remove a player from the room."""
        if player_id in self.players:
            del self.players[player_id]

    def mark_player_ready(self, player_id):
        """Mark a player as ready."""
        if player_id in self.players:
            self.players[player_id]['is_ready'] = True

    def are_all_ready(self):
        """Return True only when two players have joined and both are ready."""
        return len(self.players) == 2 and all(player['is_ready'] for player in self.players.values())

    def reset_for_game_start(self):
        """Reset scores and answers when the quiz begins."""
        self.current_question_index = 0
        self.selected_questions = random.sample(QUESTIONS, GAME_QUESTION_COUNT)
        self.game_started = True
        self.game_ended = False
        self.is_evaluating = False
        for player in self.players.values():
            player['score'] = 0
            player['current_answer'] = None
            player['answers'] = []

    def get_player_statuses(self):
        """Return player names and ready statuses for the waiting room."""
        return [
            {'id': player['id'], 'name': player['name'], 'is_ready': player['is_ready']}
            for player in self.players.values()
        ]

    def get_question_data(self):
        """Return the current question without revealing the correct answer."""
        question = self.selected_questions[self.current_question_index]
        return {
            'id': question['id'],
            'question': question['question'],
            'options': question['options'],
        }

    def submit_answer(self, player_id, answer_index):
        """Save a player's answer for the current question."""
        if player_id in self.players and self.players[player_id]['current_answer'] is None:
            self.players[player_id]['current_answer'] = answer_index

    def have_all_players_answered(self):
        """Return True when every connected player has answered."""
        return len(self.players) == 2 and all(
            player['current_answer'] is not None for player in self.players.values()
        )

    def evaluate_answers(self):
        """Mark answers and update scores."""
        question = self.selected_questions[self.current_question_index]
        for player in self.players.values():
            selected_answer = player['current_answer']
            is_correct = selected_answer == question['correct']

            if is_correct:
                player['score'] += 1

            player['answers'].append({
                'question_id': question['id'],
                'selected': selected_answer,
                'is_correct': is_correct,
            })
            player['current_answer'] = None

    def move_to_next_question(self):
        """Move to the next question and return whether one exists."""
        self.current_question_index += 1
        return self.current_question_index < len(self.selected_questions)

    def get_scores(self):
        """Return current scores keyed by player id."""
        return {
            player['id']: {'name': player['name'], 'score': player['score']}
            for player in self.players.values()
        }

    def get_winner(self):
        """Return final scores and a winner; ties show as Draw."""
        scores = {player['name']: player['score'] for player in self.players.values()}
        max_score = max(scores.values())
        winners = [name for name, score in scores.items() if score == max_score]
        winner_name = 'Draw' if len(winners) > 1 else winners[0]
        return {'name': winner_name, 'score': max_score, 'scores': scores}


def get_room_for_player(player_id):
    """Find the room containing a socket id."""
    for room_code, room in rooms.items():
        if player_id in room.players:
            return room_code, room
    return None, None


def emit_waiting_room_update(room_code):
    """Send the latest waiting-room player list to everyone in a room."""
    room = rooms.get(room_code)
    if not room:
        return

    socketio.emit('room_updated', {
        'room_code': room_code,
        'players': room.get_player_statuses(),
    }, to=room_code)


@app.route('/')
def index():
    """Serve the main game page."""
    return render_template('index.html')


@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    print(f'Client connected: {request.sid}')


@socketio.on('disconnect')
def handle_disconnect():
    """Remove disconnected players and update remaining players."""
    sid = request.sid
    room_code, room = get_room_for_player(sid)

    if room:
        room.remove_player(sid)
        socketio.emit('player_left', {
            'players_count': len(room.players),
            'players': room.get_player_statuses(),
        }, to=room_code)

        if len(room.players) == 0:
            if room.question_timeout:
                room.question_timeout.cancel()
            del rooms[room_code]

    print(f'Client disconnected: {sid}')


@socketio.on('create_room')
def handle_create_room(data):
    """Create a new game room."""
    room_code = data.get('room_code', '').strip().upper()
    player_name = data.get('player_name', '').strip()
    sid = __import__('flask').request.sid

    if not room_code or not player_name:
        emit('error', {'message': 'Room code and player name required'})
        return

    if room_code in rooms:
        emit('error', {'message': 'Room already exists'})
        return

    room = GameRoom(room_code)
    room.add_player(sid, player_name)
    rooms[room_code] = room
    join_room(room_code)

    emit('room_created', {
        'room_code': room_code,
        'players': room.get_player_statuses()
    })

    print(f'Room created: {room_code} by {player_name}')

@socketio.on('join_room')
def handle_join_room(data):
    """Join an existing game room."""
    room_code = data.get('room_code', '').strip().upper()
    player_name = data.get('player_name', '').strip()
    sid = __import__('flask').request.sid

    if not room_code or not player_name:
        emit('error', {'message': 'Room code and player name required'})
        return

    if room_code not in rooms:
        emit('error', {'message': 'Room not found'})
        return

    room = rooms[room_code]

    if not room.add_player(sid, player_name):
        emit('error', {'message': 'Room is full'})
        return

    join_room(room_code)

    # Send the joining player to the waiting room
    emit('room_joined', {
        'room_code': room_code,
        'players': room.get_player_statuses()
    })

    # Update everyone in the room, including player 1
    socketio.emit('room_updated', {
        'room_code': room_code,
        'players': room.get_player_statuses()
    }, to=room_code)

    print(f'{player_name} joined room: {room_code}')


@socketio.on('player_ready')
def handle_player_ready(data):
    """Handle player ready status."""
    sid = __import__('flask').request.sid

    for room_code, room in rooms.items():
        if sid in room.players:
            room.mark_player_ready(sid)

            socketio.emit('room_updated', {
                'room_code': room_code,
                'players': room.get_player_statuses()
            }, to=room_code)

            if room.are_all_ready():
                socketio.emit('both_players_ready', {
                    'message': 'Both players ready! Starting game...'
                }, to=room_code)

                socketio.start_background_task(start_game_delayed, room_code)

            break


def start_game_delayed(room_code):
    """Wait briefly on the starting screen, then start the quiz."""
    time.sleep(2)
    start_game(room_code)


def start_game(room_code):
    """Start the quiz game and send question one."""
    room = rooms.get(room_code)
    if not room or not room.are_all_ready():
        return

    room.reset_for_game_start()

    socketio.emit('game_started', {
        'question': room.get_question_data(),
        'question_number': 1,
        'total_questions': len(room.selected_questions),
        'scores': room.get_scores(),
    }, to=room_code)

    schedule_question_timeout(room_code)


def schedule_question_timeout(room_code):
    """Schedule automatic question evaluation after 5 seconds."""
    room = rooms.get(room_code)
    if not room or room.game_ended:
        return

    if room.question_timeout:
        room.question_timeout.cancel()

    room.question_timeout = threading.Timer(5.0, evaluate_and_next_question, args=[room_code])
    room.question_timeout.start()


@socketio.on('submit_answer')
def handle_submit_answer(data):
    """Record an answer and evaluate early if both players have answered."""
    sid = request.sid
    answer_index = data.get('answer_index')
    room_code, room = get_room_for_player(sid)

    if not room or not room.game_started or room.game_ended:
        return

    room.submit_answer(sid, answer_index)

    if room.have_all_players_answered() and not room.is_evaluating:
        room.is_evaluating = True
        if room.question_timeout:
            room.question_timeout.cancel()
        socketio.start_background_task(evaluate_after_short_delay, room_code)


def evaluate_after_short_delay(room_code):
    """Briefly show answer-submitted feedback before moving on."""
    time.sleep(0.5)
    evaluate_and_next_question(room_code)


def evaluate_and_next_question(room_code):
    """Evaluate current answers, then either send next question or end the game."""
    room = rooms.get(room_code)
    if not room or room.game_ended:
        return

    if room.question_timeout:
        room.question_timeout.cancel()
        room.question_timeout = None

    room.evaluate_answers()
    room.is_evaluating = False

    if room.move_to_next_question():
        socketio.emit('question_answered', {
            'question': room.get_question_data(),
            'question_number': room.current_question_index + 1,
            'total_questions': len(room.selected_questions),
            'scores': room.get_scores(),
        }, to=room_code)
        schedule_question_timeout(room_code)
    else:
        end_game(room_code)


def end_game(room_code):
    """End the game and send final results."""
    room = rooms.get(room_code)
    if not room:
        return

    room.game_ended = True
    if room.question_timeout:
        room.question_timeout.cancel()
        room.question_timeout = None

    winner = room.get_winner()
    socketio.emit('game_ended', {
        'final_scores': winner['scores'],
        'winner': {'name': winner['name'], 'score': winner['score']},
    }, to=room_code)


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
