// Initialize socket connection
const socket = io();

function getDeviceId() {
    let deviceId = localStorage.getItem('matchup_device_id');

    if (!deviceId) {
        deviceId = crypto.randomUUID();
        localStorage.setItem('matchup_device_id', deviceId);
    }

    return deviceId;
}

const sounds = {
    click: new Audio('/static/sounds/click.mp3'),
    tick: new Audio('/static/sounds/tick.mp3'),
    correct: new Audio('/static/sounds/correct.mp3'),
    wrong: new Audio('/static/sounds/wrong.mp3')
};

function playSound(sound) {
    sound.currentTime = 0;
    sound.play().catch(() => {});
}

// Game state management
const state = {
    gameState: 'menu',
    roomCode: '',
    playerName: '',
    players: [],
    currentQuestion: null,
    questionNumber: 0,
    totalQuestions: 10,
    timeLeft: 5,
    answered: false,
    screenFlash: '',
    scores: {},
    finalScores: {},
    winner: null,
    isPlayerReady: false,
    isHost: false,
    rematchPlayers: [],
    rematchRequested: false,
    isSuddenDeath: false,
    suddenDeathMessage: '',
    isSearching: false,
    authUser: null,
    authMode: 'login',
    showAuthModal: false,
    isRankedGame: false,
};

async function checkAuthStatus() {
    try {
        const response = await fetch('/api/me');

        const data = await response.json();

        if (data.logged_in) {
            state.authUser = data.user;
        } else {
            state.authUser = null;
        }

        render();

    } catch (error) {
        console.error('Failed to check auth status:', error);
    }
}

// Socket event listeners
socket.on('error', (data) => {
    alert(`Error: ${data.message}`);
});

socket.on('room_created', (data) => {
    state.roomCode = data.room_code;
    state.players = data.players;
    state.isHost = data.is_host;
    state.gameState = 'waiting';
    state.isPlayerReady = false;
    render();
});

socket.on('room_joined', (data) => {
    state.roomCode = data.room_code;
    state.players = data.players;
    state.isHost = data.is_host;
    state.gameState = 'waiting';
    state.isPlayerReady = false;
    render();
});

socket.on('player_joined', (data) => {
    state.players = data.players;
    render();
});

socket.on('ready_status_updated', (data) => {
    state.players = data.players;
    render();
});

socket.on('both_players_ready', () => {
    state.gameState = 'starting';
    render();
});

socket.on('player_left', (data) => {
    state.players = data.players || [];

    if (state.gameState !== 'menu') {
        alert('The other player left the room.');
        state.gameState = 'waiting';
        state.isPlayerReady = false;
        render();
    }
});

socket.on('game_started', (data) => {
    state.currentQuestion = data.question;
    state.questionNumber = data.question_number;
    state.totalQuestions = data.total_questions;
    state.scores = data.scores || {};
    state.gameState = 'quiz';
    state.timeLeft = 5;
    state.answered = false;
    state.answerResult = null;
    state.screenFlash = '';
    startTimer();
    render();
});

socket.on('question_answered', (data) => {
    state.currentQuestion = data.question;
    state.questionNumber = data.question_number;
    state.totalQuestions = data.total_questions;
    state.scores = data.scores;
    state.timeLeft = 5;
    state.answered = false;
    state.answerResult = null;
    state.screenFlash = '';
    startTimer();
    render();
});

socket.on('game_ended', async (data) => {
    if (timerInterval) clearInterval(timerInterval);

    state.gameState = 'results';
    state.finalScores = data.final_scores;
    state.winner = data.winner;
    state.rematchPlayers = [];
    state.rematchRequested = false;
    state.isRankedGame = data.is_ranked || false;

    await checkAuthStatus();

    render();
});

socket.on('room_updated', (data) => {
    state.roomCode = data.room_code;
    state.players = data.players;
    state.gameState = 'waiting';

    const currentPlayer = state.players.find(player => player.name === state.playerName);

    if (currentPlayer) {
        state.isPlayerReady = currentPlayer.is_ready;
    }

    render();
});

socket.on('search_cancelled', () => {
    state.isSearching = false;
    state.gameState = 'menu';
    render();
});

socket.on('answer_result', (data) => {
    const myResult = data.results[socket.id];

    if (!myResult) return;

    state.answerResult = myResult;
    state.screenFlash = myResult.is_correct ? 'flash-correct' : 'flash-wrong';

    if (myResult.is_correct) {
        playSound(sounds.correct);
    } else {
        playSound(sounds.wrong);
    }

    render();
});

socket.on('room_closed', (data) => {

    alert(data.message);

    setTimeout(() => {
        resetToMenu();
    }, 3000);

});

socket.on('rematch_updated', (data) => {
    state.rematchPlayers = data.players || [];

    const currentPlayer = state.rematchPlayers.find(player => player.name === state.playerName);

    if (currentPlayer) {
        state.rematchRequested = currentPlayer.wants_rematch;
    }

    render();
});

socket.on('rematch_ready', (data) => {
    if (timerInterval) clearInterval(timerInterval);

    state.gameState = 'waiting';
    state.roomCode = data.room_code;
    state.players = data.players;
    state.currentQuestion = null;
    state.questionNumber = 0;
    state.timeLeft = 5;
    state.answered = false;
    state.answerResult = null;
    state.screenFlash = '';
    state.scores = {};
    state.finalScores = {};
    state.winner = null;
    state.isPlayerReady = false;
    state.rematchPlayers = [];
    state.rematchRequested = false;

    render();
});

socket.on('sudden_death_starting', (data) => {
    if (timerInterval) clearInterval(timerInterval);

    state.gameState = 'suddenDeathStarting';
    state.isSuddenDeath = true;
    state.suddenDeathMessage = data.message;
    state.answered = false;
    state.answerResult = null;
    state.screenFlash = '';

    render();
});

socket.on('sudden_death_question', (data) => {
    state.gameState = 'suddenDeath';
    state.currentQuestion = data.question;
    state.scores = data.scores || {};
    state.timeLeft = 5;
    state.answered = false;
    state.answerResult = null;
    state.screenFlash = '';

    startTimer();
    render();
});

socket.on('searching_for_match', (data) => {
    state.isSearching = true;
    state.gameState = 'searching';
    render();
});

socket.on('match_found', (data) => {
    state.roomCode = data.room_code;
    state.players = data.players;
    state.isHost = data.is_host;
    state.gameState = 'waiting';
    state.isPlayerReady = false;
    state.isSearching = false;

    render();
});


// Timer management
let timerInterval = null;

function startTimer() {
    if (timerInterval) clearInterval(timerInterval);

    state.timeLeft = 5;

    timerInterval = setInterval(() => {
        state.timeLeft -= 1;
        if (state.timeLeft <= 3 && state.timeLeft > 0) {
            playSound(sounds.tick);
        }
        render();

        if (state.timeLeft <= 0) {
            clearInterval(timerInterval);
        }
    }, 1000);
}

// Event handlers
function handleCreateRoom(e) {
    e.preventDefault();

    const roomCode = document.getElementById('roomCode').value.trim();
    const playerName = state.authUser
    ? state.authUser.username
    : document.getElementById('playerName').value.trim();

    if (roomCode && playerName) {
        state.roomCode = roomCode.toUpperCase();
        state.playerName = playerName;
        socket.emit('create_room', {
            room_code: roomCode,
            player_name: playerName
        });
    }
}

function handleJoinRoom(e) {
    e.preventDefault();

    const roomCode = document.getElementById('joinRoomCode').value.trim();
    const playerName = state.authUser
    ? state.authUser.username
    : document.getElementById('joinPlayerName').value.trim();

    if (roomCode && playerName) {
        state.roomCode = roomCode.toUpperCase();
        state.playerName = playerName;
        socket.emit('join_room', {
            room_code: roomCode,
            player_name: playerName
        });
    }
}

function handleReadyClick() {
    if (!state.isPlayerReady) {
        state.isPlayerReady = true;
        socket.emit('player_ready', {});
        render();
    }
}

function handleCloseRoom() {
    socket.emit('close_room');
}

function handleAnswerClick(index) {
    if (!state.answered) {
        playSound(sounds.click);
        state.answered = true;
        state.screenFlash = 'flash-locked';
        socket.emit('submit_answer', {
            answer_index: index
        });
        render();
    }
}

function handlePlayAgain() {
    if (timerInterval) clearInterval(timerInterval);

    state.gameState = 'menu';
    state.roomCode = '';
    state.playerName = '';
    state.players = [];
    state.currentQuestion = null;
    state.questionNumber = 0;
    state.timeLeft = 5;
    state.answered = false;
    state.scores = {};
    state.finalScores = {};
    state.winner = null;
    state.isPlayerReady = false;

    render();
}

function handleRematchClick() {
    if (!state.rematchRequested) {
        state.rematchRequested = true;
        socket.emit('request_rematch');
        render();
    }
}

function openAuthModal(mode) {
    state.authMode = mode;
    state.showAuthModal = true;
    render();
}

function closeAuthModal() {
    state.showAuthModal = false;
    render();
}

function handleSearchMatch(e) {
    e.preventDefault();

    const playerName = state.authUser
    ? state.authUser.username
    : document.getElementById('searchPlayerName').value.trim();

    if (!playerName) {
        alert('Please enter your name.');
        return;
    }

    state.playerName = playerName;
    state.isSearching = true;
    state.gameState = 'searching';

    socket.emit('search_match', {
        player_name: playerName,
        device_id: getDeviceId()
    });

    render();
}

function handleCancelSearch() {
    state.isSearching = false;
    state.gameState = 'menu';
    socket.emit('cancel_search');
    render();
}

async function handleRegister(e) {
    e.preventDefault();

    const username = document.getElementById('authUsername').value.trim();
    const email = document.getElementById('authEmail').value.trim();
    const password = document.getElementById('authPassword').value;

    try {
        const response = await fetch('/api/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username,
                email,
                password
            })
        });

        const data = await response.json();

        if (!data.success) {
            alert(data.message);
            return;
        }

        state.authUser = data.user;
        state.playerName = data.user.username;
        state.showAuthModal = false;

        render();

    } catch (error) {
        alert('Something went wrong while creating your account.');
    }
}

async function handleLogin(e) {
    e.preventDefault();

    const email = document.getElementById('authEmail').value.trim();
    const password = document.getElementById('authPassword').value;

    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email,
                password
            })
        });

        const data = await response.json();

        if (!data.success) {
            alert(data.message);
            return;
        }

        state.authUser = data.user;

        socket.disconnect();
        socket.connect();

        state.playerName = data.user.username;
        state.showAuthModal = false;

        render();

    } catch (error) {
        alert('Something went wrong while logging in.');
    }
}

function handleLeaveRoom() {
    socket.emit('leave_room');

    state.gameState = 'menu';
    state.roomCode = '';
    state.players = [];
    state.isPlayerReady = false;
    state.isHost = false;

    render();
}

async function handleLogout() {
    try {
        await fetch('/api/logout', {
            method: 'POST'
        });

        state.authUser = null;
        state.playerName = '';
        state.showAuthModal = false;
        state.isSearching = false;
        state.gameState = 'menu';

        render();

    } catch (error) {
        alert('Something went wrong while logging out.');
    }
}

function resetToMenu() {

    if (timerInterval) clearInterval(timerInterval);

    state.gameState = 'menu';
    state.roomCode = '';
    state.players = [];
    state.currentQuestion = null;
    state.questionNumber = 0;

    state.answered = false;
    state.answerResult = null;
    state.screenFlash = '';

    state.scores = {};
    state.finalScores = {};
    state.winner = null;

    state.isPlayerReady = false;
    state.isHost = false;

    render();
}

// Rendering functions
function render() {
    const root = document.getElementById('root');

    if (state.gameState === 'menu') {
        root.innerHTML = renderMenu();
    } else if (state.gameState === 'searching') {
    root.innerHTML = renderSearching();
    } else if (state.gameState === 'waiting') {
        root.innerHTML = renderWaiting();
    } else if (state.gameState === 'starting') {
        root.innerHTML = renderStarting();
    } else if (state.gameState === 'quiz') {
        root.innerHTML = renderQuiz();
    } else if (state.gameState === 'results') {
        root.innerHTML = renderResults();
    } else if (state.gameState === 'suddenDeathStarting') {
        root.innerHTML = renderSuddenDeathStarting();
    } else if (state.gameState === 'suddenDeath') {
        root.innerHTML = renderQuiz();
    }
}

function renderMenu() {
    return `
        <div class="app">
            <div class="menu-container">
                <div class="home-grid">
                    <div class="quick-match-card">
                        <h2>Quick Match</h2>
                        <p class="info">Search online and play against another player instantly.</p>

                        <form onsubmit="handleSearchMatch(event)">
                            ${state.authUser ? `
                                <div class="account-player-box">
                                    Playing as <strong>${state.authUser.username}</strong>
                                </div>
                            ` : `
                                <input
                                    type="text"
                                    id="searchPlayerName"
                                    placeholder="Enter your name"
                                    maxlength="20"
                                    required
                                    ${state.isSearching ? 'disabled' : ''}
                                />
                            `}

                            <button type="submit" class="btn btn-primary">
                                Search for Match
                            </button>
                        </form>
                    </div>

                    <div class="centre-brand-card">
                        <img src="/static/matchup-logo.png" class="main-logo" alt="MatchUp logo">
                        <h1 class="menu-title">MATCH<span>UP</span></h1>
                        <p class="brand-tagline">Football knowledge. Head to head.</p>
                    </div>

                    ${renderProfileCard()}
                </div>

                <div class="private-row">
                    <div class="menu-section">
                        <h2>Create Private Room</h2>
                        <form onsubmit="handleCreateRoom(event)">
                            <input type="text" id="roomCode" placeholder="Room code" maxlength="20" required />
                            ${state.authUser ? `
                                <div class="account-player-box">Playing as <strong>${state.authUser.username}</strong></div>
                            ` : `
                                <input type="text" id="playerName" placeholder="Your name" maxlength="20" required />
                            `}
                            <button type="submit" class="btn btn-secondary">Create</button>
                        </form>
                    </div>

                    <div class="menu-section">
                        <h2>Join Private Room</h2>
                        <form onsubmit="handleJoinRoom(event)">
                            <input type="text" id="joinRoomCode" placeholder="Room code" maxlength="20" required />
                            ${state.authUser ? `
                                <div class="account-player-box">Playing as <strong>${state.authUser.username}</strong></div>
                            ` : `
                                <input type="text" id="joinPlayerName" placeholder="Your name" maxlength="20" required />
                            `}
                            <button type="submit" class="btn btn-secondary">Join</button>
                        </form>
                    </div>
                </div>
            </div>
            ${state.showAuthModal ? renderAuthModal() : ''}
        </div>
    `;
}

function renderProfileCard() {
    if (!state.authUser) {
        return `
            <div class="profile-card">
                <h2>Player Profile</h2>
                <p class="info">Login to track your rank, points and match history.</p>
                <button class="btn btn-primary" onclick="openAuthModal('login')">Login</button>
                <button class="btn btn-secondary" onclick="openAuthModal('register')">Sign Up</button>
            </div>
        `;
    }

    return `
        <div class="profile-card">
            <h2>Player Profile</h2>
            <div class="profile-name">👤 ${state.authUser.username}</div>

            <div
                class="profile-rank"
                style="background: ${state.authUser.rank?.color || '#9CA3AF'};"
            >
                ${state.authUser.rank?.name || 'Sunday League'}
            </div>

            <div class="profile-points">
                ${state.authUser.ranked_points ?? 0} RP
            </div>

            <p class="profile-small">More stats coming soon</p>

            <hr class="profile-divider">
            <button
                class="btn btn-secondary profile-logout-btn"
                onclick="handleLogout()"
            >
                Log Out
            </button>
        </div>
    `;
}

function renderWaiting() {
    const bothPlayersJoined = state.players.length === 2;

    return `
        <div class="app">
            <div class="waiting-container">
                <h1><span class="brand-mini"></span> MATCH ROOM: ${state.roomCode}</h1>

                <p class="info">
                    ${bothPlayersJoined
                        ? 'Both players are in. Ready up to start the MatchUp.'
                        : 'Waiting for your opponent to join...'}
                </p>

                <div class="players-list">
                    ${state.players.map((player, index) => `
                        <div class="player-item">
                            <span class="player-name ${index === 0 ? 'player-1' : 'player-2'}">👤 ${player.name}</span>
                            <span class="player-status ${player.is_ready ? 'ready' : 'not-ready'}">
                                ${player.is_ready ? '✅ READY' : '⏸ WAITING'}
                            </span>
                        </div>
                    `).join('')}
                </div>

                <p class="players-count">👥 ${state.players.length} / 2 Players</p>

                ${bothPlayersJoined ? `
                    <button
                        class="btn btn-primary ${state.isPlayerReady ? 'ready-btn-active' : ''}"
                        onclick="handleReadyClick()"
                        ${state.isPlayerReady ? 'disabled' : ''}
                    >
                        ${state.isPlayerReady ? 'READY' : 'Ready Up'}
                    </button>
                ${state.isHost ? `
                    <button
                        class="btn btn-danger"
                        onclick="handleCloseRoom()"
                    >
                        ❌ Close Room
                    </button>
                ` : ''}
                ` : `
                <button class="btn btn-danger" onclick="handleLeaveRoom()">
                    Leave Room
                </button>
                    <div class="spinner"></div>
                    <p class="info">Share this room code: <strong style="font-size: 18px; color: #ff6b35;">${state.roomCode}</strong></p>
                `}
            </div>
        </div>
    `;
}

function renderSearching() {
    return `
        <div class="app">
            <div class="waiting-container">
                <div class="brand-lockup">
                    <img src="/static/matchup-logo.png" class="main-logo" alt="MatchUp logo">
                </div>

                <h1 class="screen-title">Searching...</h1>

                <p class="info">
                    Looking for an opponent for <strong>${state.playerName}</strong>
                </p>

                <div class="spinner"></div>

                <button
                    type="button"
                    class="btn btn-secondary"
                    onclick="handleCancelSearch()"
                >
                    Cancel Search
                </button>
            </div>
        </div>
    `;
}

function renderStarting() {
    return `
        <div class="app">
            <div class="starting-container">
                <h1><span class="brand-mini"></span> MATCH<span>UP</span></h1>

                <div class="starting-players">
                    ${state.players.map(player => `
                        <div class="starting-player">👤 ${player.name}</div>
                    `).join('')}
                </div>

                <p class="starting-text">Football knowledge. Head to head.</p>
                <div class="countdown">🎮</div>
            </div>
        </div>
    `;
}

function renderSuddenDeathStarting() {
    return `
        <div class="app">
            <div class="starting-container sudden-death-container">
                <h1>GOLDEN GOAL</h1>

                <p class="starting-text">
                    ${state.suddenDeathMessage || 'Fastest correct answer wins!'}
                </p>

                <p class="info">
                    The match is tied. One final question decides it.
                </p>

                <div class="countdown">⏱️</div>
            </div>
        </div>
    `;
}

function renderAuthModal() {
    const isRegister = state.authMode === 'register';

    return `
        <div class="auth-modal-backdrop">
            <div class="auth-modal">
                <button class="auth-close" onclick="closeAuthModal()">×</button>

                <h2>${isRegister ? 'Create Account' : 'Login'}</h2>

                <form onsubmit="${isRegister ? 'handleRegister(event)' : 'handleLogin(event)'}">
                    ${isRegister ? `
                        <input
                            type="text"
                            id="authUsername"
                            placeholder="Username"
                            maxlength="20"
                            required
                        />
                    ` : ''}

                    <input
                        type="email"
                        id="authEmail"
                        placeholder="Email"
                        required
                    />

                    <input
                        type="password"
                        id="authPassword"
                        placeholder="Password"
                        minlength="8"
                        required
                    />

                    <button type="submit" class="btn btn-primary">
                        ${isRegister ? 'Sign Up' : 'Login'}
                    </button>
                </form>

                <p class="auth-switch">
                    ${isRegister
                        ? 'Already have an account?'
                        : 'Need an account?'}
                    <button
                        onclick="openAuthModal('${isRegister ? 'login' : 'register'}')"
                    >
                        ${isRegister ? 'Login' : 'Sign Up'}
                    </button>
                </p>
            </div>
        </div>
    `;
}

function renderQuiz() {
    if (!state.currentQuestion) {
        return `
            <div class="app ${state.screenFlash}">
                <div class="quiz-container">
                    <h2>Loading next question...</h2>
                </div>
            </div>
        `;
    }

    return `
        <div class="app ${state.screenFlash}">
            <div class="quiz-container">
                <div class="quiz-header">
                    <div class="question-counter">
                        ${state.gameState === 'suddenDeath'
                            ? 'GOLDEN GOAL · FASTEST CORRECT ANSWER WINS'
                            : `⚽ Question ${state.questionNumber}/${state.totalQuestions}`}
                    </div>

                    <div class="timer">
                        <span class="time ${state.timeLeft <= 2 ? 'warning' : ''}">
                            ${state.timeLeft}s
                        </span>
                    </div>
                </div>

                <div class="quiz-content">
                    <h2 class="question-text">${state.currentQuestion.question}</h2>

                    <div class="options-grid">
                        ${state.currentQuestion.options.map((option, index) => `
                            <button
                                class="option-btn ${state.answered ? 'disabled' : ''}"
                                onclick="handleAnswerClick(${index})"
                                ${state.answered ? 'disabled' : ''}
                            >
                                <span class="option-label">${String.fromCharCode(65 + index)}</span>
                                <span class="option-text">${option}</span>
                            </button>
                        `).join('')}
                    </div>
                </div>

                <div class="scores-display">
                    ${Object.entries(state.scores).map(([id, data]) => `
                        <div class="score-item">
                            <span class="player-name">👤 ${data.name}</span>
                            <span class="score-value">${data.score}</span>
                        </div>
                    `).join('')}
                </div>

                ${state.answerResult ? `
                    <div class="answer-result ${state.answerResult.is_correct ? 'correct' : 'wrong'}">
                        ${state.answerResult.is_correct ? '✅ Correct!' : '❌ Wrong!'}
                    </div>
                ` : state.answered ? `
                    <div class="answer-submitted">🔒 Answer Locked In!</div>
                ` : ''}
            </div>
        </div>
    `;
}

function renderAuthBar() {
    if (state.authUser) {
        return `
            <div class="auth-bar">
                <div class="auth-profile">
                    <span class="auth-user">👤 ${state.authUser.username}</span>

                    <span
                        class="rank-badge"
                        style="background: ${state.authUser.rank?.color || '#9CA3AF'};"
                    >
                        ${state.authUser.rank?.name || 'Sunday League'}
                    </span>

                    <span class="rank-points">
                        ${state.authUser.ranked_points ?? 0} RP
                    </span>
                </div>

                <button class="auth-btn" onclick="handleLogout()">Logout</button>
            </div>
        `;
    }

    return `
        <div class="auth-bar">
            <button class="auth-btn" onclick="openAuthModal('login')">Login</button>
            <button class="auth-btn auth-btn-primary" onclick="openAuthModal('register')">Sign Up</button>
        </div>
    `;
}

function renderResults() {
    return `
        <div class="app">
            ${renderAuthBar()}
            <div class="results-container">
                <h1><span class="brand-mini"></span> FULL TIME</h1>
                <div class="match-type-badge ${state.isRankedGame ? 'ranked' : 'private'}">
                    ${state.isRankedGame ? 'Ranked Match' : 'Private Match'}
                </div>

                <div class="winner-section">
                    ${state.winner.sudden_death_times ? `
                        <div class="sudden-death-results">
                            <h3>Golden Goal Results</h3>

                            ${state.winner.sudden_death_times.map(player => `
                                <div class="sudden-death-player">
                                    <span>
                                        ${player.is_correct ? '✅' : '❌'}
                                        ${player.name}
                                    </span>

                                    <span>
                                        ${player.timed_out
                                        ? 'No answer'
                                        : player.answer_time !== null
                                            ? `${player.answer_time.toFixed(2)}s`
                                            : '--'}
                                    </span>
                                </div>
                            `).join('')}
                        </div>
                    ` : ''}

                    <h2 class="winner-text">
                        ${state.winner.sudden_death_draw
                            ? 'GOLDEN GOAL DRAW'
                            : state.winner.won_by_sudden_death
                                ? `${state.winner.name} WINS BY GOLDEN GOAL!`
                                : state.winner.name === 'Draw'
                                    ? '🤝 DRAW! 🤝'
                                    : `🏆 ${state.winner.name} WINS! 🏆`}
                    </h2>

                    <p class="winner-score">
                        ${state.winner.sudden_death_draw
                            ? 'Both players missed the Golden Goal question.'
                            : state.winner.won_by_sudden_death
                                ? 'Fastest correct answer decided the match.'
                                : `Final Score: ${state.winner.score} / 10 Questions`}
                    </p>
                </div>

                <div class="final-scores">
                    <h3>📊 Final Standings</h3>

                    <div class="scores-list">
                        ${Object.entries(state.finalScores).map(([name, score], index) => `
                            <div class="score-row ${name === state.winner.name ? 'winner-row' : ''}">
                                <span class="rank">${index === 0 ? '🥇' : '🥈'}</span>
                                <span class="name">${name}</span>
                                <span class="points">${score} ⭐</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
                <div class="rematch-section">
                <h3>🔁 Rematch?</h3>

                <div class="players-list">
                    ${state.rematchPlayers.length > 0 ? state.rematchPlayers.map(player => `
                        <div class="player-item">
                            <span class="player-name">👤 ${player.name}</span>
                            <span class="player-status ${player.wants_rematch ? 'ready' : 'not-ready'}">
                                ${player.wants_rematch ? '✅ REMATCH' : '⏸ WAITING'}
                            </span>
                        </div>
                    `).join('') : `
                        <p class="info">Waiting for rematch votes...</p>
                    `}
                </div>

                <button
                    class="btn btn-primary ${state.rematchRequested ? 'ready-btn-active' : ''}"
                    onclick="handleRematchClick()"
                    ${state.rematchRequested ? 'disabled' : ''}
                >
                    ${state.rematchRequested ? '✅ Rematch Requested' : '🔁 Request Rematch'}
                </button>

                <button class="btn btn-secondary" onclick="handlePlayAgain()">
                    ⬅️ Back to Menu
                </button>
            </div>
            </div>
        </div>
    `;
}



// Initial render
document.addEventListener('DOMContentLoaded', () => {
    checkAuthStatus();
});