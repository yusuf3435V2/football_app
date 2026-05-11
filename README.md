# Multiplayer Quiz Application

A real-time 2-player multiplayer quiz game built with Python/Flask and Socket.io. Players create or join a room using a room code and compete to answer 10 questions correctly within 5 seconds each. **Correct answers are kept secret on the backend** to prevent cheating.

## Features

- ✅ Real-time multiplayer using Socket.io
- ✅ Room creation and join system with custom room codes
- ✅ 10 quiz questions with 4 multiple-choice options
- ✅ 5-second timer per question
- ✅ Live score tracking
- ✅ Winner determination based on correct answers
- ✅ **Backend-side answer validation** (no cheating via browser inspection)
- ✅ Responsive UI with modern design
- ✅ Functional Python backend with one-line docstrings

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

Start the Flask server:
```bash
python app.py
```

The application will run on: `http://localhost:5000`

## How to Play

1. **Create Room**: Enter a room code (e.g., "quiz123") and your name, click "Create & Join"
2. **Share Room Code**: Give the room code to your friend
3. **Join Room**: They enter the same room code and their name, click "Join Game"
4. **Wait for Second Player**: Once both players join, the game starts automatically in 2 seconds
5. **Answer Questions**: Click on an answer option within 5 seconds
6. **Check Score**: View live scores as questions are answered
7. **See Results**: After 10 questions, see the winner and final scores
8. **Play Again**: Click "Play Again" to return to the menu

## Project Structure

```
football_app/
├── app.py                      # Flask + Socket.io server
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── templates/
│   └── index.html             # HTML entry point
└── static/
    ├── app.js                 # Frontend JavaScript logic
    └── style.css              # Styles
```

## Technology Stack

- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Backend**: Python 3, Flask, Flask-SocketIO
- **Real-time Communication**: Socket.io
- **Deployment**: Flask development server

## Security Features

### Answer Validation
- **Correct answers are stored ONLY on the server** in the `QUESTIONS` array
- Frontend receives: question ID, question text, and options (NO correct answer)
- Player submissions are validated server-side before updating scores
- Even if frontend is inspected, cheating is impossible

### Data Flow
1. Frontend submits answer index to server
2. Server checks against stored correct answer
3. Server updates player score
4. Server broadcasts updated scores to both players

## Game Rules

- 10 questions total
- Each question has 5 seconds to answer
- Answers are submitted by clicking an option
- Score increases by 1 for each correct answer
- Both players answer simultaneously
- If both players answer before 5 seconds, game advances immediately
- If time runs out, unanswered questions score 0 points
- Winner is determined by highest final score
- Both players see scores update in real-time
