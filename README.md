# Football Quiz Multiplayer App

This project is a real-time multiplayer football quiz game built with Python, Flask, and Socket.IO. Two players can join a room, answer football-themed questions, and compete for the highest score. The app also supports quick matchmaking, account registration/login, ranked points, and a sudden-death tie-breaker.

## What the app does right now

The current version includes:

- A real-time 2-player quiz experience using Flask-SocketIO
- Room creation and joining with a custom room code
- Quick-match matchmaking for finding an opponent automatically
- A waiting room with ready-state checks before the game begins
- A 10-question quiz round with football trivia
- A timed question flow (currently set to 7 seconds per question)
- Live score updates after each answer
- A sudden-death round when the match ends in a tie
- Basic account features: register, log in, log out, and session-based access
- Ranked points and rank badges such as “Wonderkid”, “Star Player”, and “Icon”
- A simple responsive web interface powered by HTML, CSS, and JavaScript

## Tech stack

- Backend: Python, Flask, Flask-SocketIO
- Frontend: HTML, CSS, Vanilla JavaScript
- Real-time communication: Socket.IO
- Deployment: Gunicorn with Eventlet for async Socket.IO support
- Database: PostgreSQL (required for login, registration, and ranked points)

## Project structure

```text
football_app/
├── app.py                 # Flask server and Socket.IO game logic
├── Procfile               # Render/production start command
├── requirements.txt       # Python dependencies
├── runtime.txt            # Python version for deployment
├── static/                # Frontend assets
│   ├── app.js
│   ├── style.css
│   └── sounds/
└── templates/
    └── index.html
```

## Running locally

### 1. Clone the project

```bash
git clone <your-repo-url>
cd football_app
```

### 2. Create and activate a virtual environment

On macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

The app expects a few environment variables:

```bash
export SECRET_KEY="your-secret-key"
export DATABASE_URL="postgresql://username:password@localhost:5432/football_quiz"
```

You can also add these to a `.env` file if you prefer, but the app is currently reading directly from the environment.

### 5. Create the PostgreSQL database and users table

You need PostgreSQL running locally. Create a database and then create the `users` table so registration and login work:

```sql
CREATE DATABASE football_quiz;

\c football_quiz

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    ranked_points INTEGER DEFAULT 0
);
```

If you use a different database name, make sure `DATABASE_URL` matches it.

### 6. Start the app

```bash
python app.py
```

Then open:

```text
http://localhost:5000
```

## How to play

1. Open the app in your browser.
2. Create a room or use quick match to find an opponent.
3. Enter your name and join a room.
4. Wait for the second player to join and click ready.
5. Once both players are ready, the quiz starts automatically.
6. Answer each question before the timer runs out.
7. After the round, the app shows the winner and final scores.
8. You can request a rematch from the end screen.

## Local development notes

- The quiz questions are stored in the server code in `app.py`.
- The frontend logic lives in `static/app.js` and the page shell is in `templates/index.html`.
- The server uses Socket.IO for real-time updates, so the app should be run as a single Flask process rather than as a static page.
- If you want to test the app without authentication, you can still open the game UI, but account-based features and ranked points require a working PostgreSQL connection.

## Deploying to Render

Render is a good option for hosting this app because it supports Python web services and background workers for Socket.IO apps.

### 1. Push the project to GitHub

Make sure your repository contains:

- `app.py`
- `requirements.txt`
- `Procfile`
- `runtime.txt`
- `templates/`
- `static/`

### 2. Create a new Web Service on Render

In Render:

- Create a new Web Service
- Connect your GitHub repository
- Set the environment to Python

### 3. Configure the build and start commands

Render should use these values:

- Build Command:

```bash
pip install -r requirements.txt
```

- Start Command:

```bash
gunicorn --worker-class eventlet -w 1 app:app
```

The repository already includes a `Procfile` with the correct start command.

### 4. Add environment variables in Render

Set these in the Render dashboard:

- `SECRET_KEY`: any long random string
- `DATABASE_URL`: your PostgreSQL connection string

If you use Render’s managed PostgreSQL:

- Create a PostgreSQL database
- Copy the internal connection string into `DATABASE_URL`

### 5. Deploy

Render will install dependencies, start the app, and expose it at a public URL such as:

```text
https://your-app-name.onrender.com
```

## Important deployment note

Because this app uses Socket.IO, it is important to run it with Gunicorn and Eventlet rather than the default Flask development server. That is already handled by the provided `Procfile` and `runtime.txt`.

## Current gameplay rules

- Each match uses 10 questions.
- Each question has a short timer.
- Correct answers increase the player’s score.
- If the game ends in a tie, the app triggers sudden death.
- Sudden death is based on the fastest correct answer.
- The app shows a final winner or a draw outcome at the end of the match.

