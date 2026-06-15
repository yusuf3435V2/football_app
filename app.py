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
    {'id': 51, 'question': 'Which player scored the fastest hat-trick in Premier League history?',
        'options': ['Sergio Aguero', 'Sadio Mane', 'Robbie Fowler', 'Michael Owen'], 'correct': 1},

    {'id': 52, 'question': 'Which player has made the most Premier League appearances?',
        'options': ['Ryan Giggs', 'Gareth Barry', 'James Milner', 'Frank Lampard'], 'correct': 1},

    {'id': 53, 'question': 'Which of these players shares the record for the most Premier League red cards?',
        'options': ['Roy Keane', 'Patrick Vieira', 'John Terry', 'Nemanja Vidic'], 'correct': 1},

    {'id': 54, 'question': 'With 260 goals, who is the Premier League\'s all-time top scorer?',
        'options': ['Wayne Rooney', 'Harry Kane', 'Alan Shearer', 'Sergio Aguero'], 'correct': 2},

    {'id': 55, 'question': 'How many clubs competed in the inaugural Premier League season?',
        'options': ['18', '20', '22', '24'], 'correct': 2},

    {'id': 56, 'question': 'Which player won the Premier League Golden Boot alongside Mohamed Salah and Sadio Mane in 2018/19?',
        'options': ['Jamie Vardy', 'Pierre-Emerick Aubameyang', 'Raheem Sterling', 'Harry Kane'], 'correct': 1},

    {'id': 57, 'question': 'Who was the first player to score 100 Premier League goals?',
        'options': ['Alan Shearer', 'Thierry Henry', 'Les Ferdinand', 'Michael Owen'], 'correct': 0},

    {'id': 58, 'question': 'Which club went an entire Premier League season unbeaten?',
        'options': ['Manchester United', 'Chelsea', 'Liverpool', 'Arsenal'], 'correct': 3},

    {'id': 59, 'question': 'Who scored the winning goal in the 1999 UEFA Champions League final for Manchester United?',
        'options': ['Ole Gunnar Solskjaer', 'Teddy Sheringham', 'Dwight Yorke', 'Andy Cole'], 'correct': 0},

    {'id': 60, 'question': 'Which country did Cristiano Ronaldo make his international debut against?',
        'options': ['England', 'Kazakhstan', 'Portugal', 'Germany'], 'correct': 1},

    {'id': 61, 'question': 'Which club did Kevin De Bruyne join Manchester City from?',
        'options': ['Chelsea', 'Genk', 'Werder Bremen', 'Wolfsburg'], 'correct': 3},

    {'id': 62, 'question': 'Who won the FIFA World Cup Golden Ball in 2014?', 'options': [
        'Thomas Muller', 'James Rodriguez', 'Lionel Messi', 'Arjen Robben'], 'correct': 2},

    {'id': 63, 'question': 'Which player has won the most UEFA Champions League titles?', 'options': [
        'Cristiano Ronaldo', 'Francisco Gento', 'Luka Modric', 'Paolo Maldini'], 'correct': 1},

    {'id': 64, 'question': 'Which club did Virgil van Dijk join Liverpool from?',
        'options': ['Celtic', 'Southampton', 'Groningen', 'Lazio'], 'correct': 1},

    {'id': 65, 'question': 'Who was the top scorer at the 2010 FIFA World Cup?', 'options': [
        'David Villa', 'Wesley Sneijder', 'Thomas Muller', 'Diego Forlan'], 'correct': 2},

    {'id': 66, 'question': 'Which nation won Euro 1992 despite not originally qualifying for the tournament?',
        'options': ['Denmark', 'Sweden', 'Germany', 'Netherlands'], 'correct': 0},

    {'id': 67, 'question': 'Which player scored the winning goal in the 2014 World Cup final?',
        'options': ['Thomas Muller', 'Mario Gotze', 'Miroslav Klose', 'Andre Schurrle'], 'correct': 1},

    {'id': 68, 'question': 'Which club has won the most FA Cups?', 'options': [
        'Manchester United', 'Chelsea', 'Arsenal', 'Liverpool'], 'correct': 2},

    {'id': 69, 'question': 'Who was the first African player to win the Ballon d\'Or?',
        'options': ['Didier Drogba', 'George Weah', 'Samuel Eto\'o', 'Yaya Toure'], 'correct': 1},

    {'id': 70, 'question': 'Which club did Erling Haaland join Manchester City from?',
        'options': ['RB Salzburg', 'Molde', 'Borussia Dortmund', 'Leipzig'], 'correct': 2},
    
    {'id': 71, 'question': 'What was the name of the first FIFA World Cup trophy?', 'options': [
        'The Victory Trophy', 'The Jules Rimet Trophy', 'The FIFA Trophy', 'The Golden Cup'], 'correct': 1},

    {'id': 72, 'question': 'Which country won the first ever FIFA World Cup in 1930?',
        'options': ['Argentina', 'Brazil', 'Uruguay', 'Italy'], 'correct': 2},

    {'id': 73, 'question': 'Which country has won the most FIFA World Cups?',
        'options': ['Germany', 'Italy', 'Argentina', 'Brazil'], 'correct': 3},

    {'id': 74, 'question': 'Which of these countries has won the FIFA World Cup exactly twice?',
        'options': ['Spain', 'France', 'England', 'Argentina'], 'correct': 1},

    {'id': 75, 'question': 'Which country has reached three FIFA World Cup finals but never won the tournament?',
        'options': ['Croatia', 'Hungary', 'Netherlands', 'Czechoslovakia'], 'correct': 2},

    {'id': 76, 'question': 'Which three countries will jointly host the 2026 FIFA World Cup?', 'options': [
        'United States, Canada and Mexico', 'United States, Mexico and Costa Rica', 'Canada, Mexico and Brazil', 'United States, Canada and Jamaica'], 'correct': 0},

    {'id': 77, 'question': 'In which FIFA World Cup did Diego Maradona score the infamous "Hand of God" goal?',
        'options': ['Spain 1982', 'Mexico 1986', 'Italy 1990', 'USA 1994'], 'correct': 1},

    {'id': 78, 'question': 'Who holds the record for the most goals scored in FIFA World Cup history?',
        'options': ['Ronaldo Nazario', 'Miroslav Klose', 'Gerd Muller', 'Lionel Messi'], 'correct': 1},

    {'id': 79, 'question': 'Which person, alongside Mario Zagallo and Didier Deschamps, won the FIFA World Cup as both a player and a manager?',
        'options': ['Franz Beckenbauer', 'Vicente del Bosque', 'Cesar Luis Menotti', 'Carlos Alberto Parreira'], 'correct': 0},

    {'id': 80, 'question': 'Which English player won the FIFA World Cup Golden Boot in 1986?',
        'options': ['Gary Lineker', 'Bobby Charlton', 'Geoff Hurst', 'Peter Shilton'], 'correct': 0},
    
    {'id': 81, 'question': 'Who is the only player to have won the UEFA Champions League with three different clubs?',
        'options': ['Samuel Eto\'o', 'Cristiano Ronaldo', 'Clarence Seedorf', 'Zlatan Ibrahimovic'], 'correct': 2},

    {'id': 82, 'question': 'Which manager is one of the three to have won the UEFA Champions League three times?',
        'options': ['Sir Alex Ferguson', 'Bob Paisley', 'Jose Mourinho', 'Jupp Heynckes'], 'correct': 1},

    {'id': 83, 'question': 'In which season was the European Cup rebranded as the UEFA Champions League?',
        'options': ['1990/91', '1991/92', '1992/93', '1993/94'], 'correct': 2},

    {'id': 84, 'question': 'Which team was the first from the United Kingdom to win the European Cup?',
        'options': ['Manchester United', 'Liverpool', 'Celtic', 'Nottingham Forest'], 'correct': 2},

    {'id': 85, 'question': 'Which Romanian club is the only team from Romania to have won the European Cup/Champions League?',
        'options': ['Dinamo Bucharest', 'Rapid Bucharest', 'Universitatea Craiova', 'Steaua Bucharest'], 'correct': 3},

    {'id': 86, 'question': 'Which English club has won the European Cup/Champions League twice?',
        'options': ['Chelsea', 'Aston Villa', 'Nottingham Forest', 'Manchester City'], 'correct': 2},

    {'id': 87, 'question': 'Who is the all-time top goalscorer in UEFA Champions League history?',
        'options': ['Lionel Messi', 'Robert Lewandowski', 'Cristiano Ronaldo', 'Karim Benzema'], 'correct': 2},

    {'id': 88, 'question': 'Which manager has won the most UEFA Champions League titles?', 'options': [
        'Pep Guardiola', 'Zinedine Zidane', 'Carlo Ancelotti', 'Bob Paisley'], 'correct': 2},

    {'id': 89, 'question': 'Which outfield player appeared in UEFA Champions League finals across three different decades?',
        'options': ['Paolo Maldini', 'Ryan Giggs', 'Clarence Seedorf', 'Xavi'], 'correct': 1},
    
    {'id': 90, 'question': 'In which year was the first UEFA European Championship held?',
        'options': ['1956', '1960', '1964', '1968'], 'correct': 1},

    {'id': 91, 'question': 'Which nation has won the most UEFA European Championship titles?',
        'options': ['Germany', 'France', 'Spain', 'Italy'], 'correct': 2},

    {'id': 92, 'question': 'What is the name of the UEFA European Championship trophy?', 'options': [
        'Jules Rimet Trophy', 'Henri Delaunay Trophy', 'Artemio Franchi Trophy', 'UEFA Nations Cup'], 'correct': 1},

    {'id': 93, 'question': 'Who scored the most goals in a single UEFA European Championship tournament?',
        'options': ['Cristiano Ronaldo', 'Antoine Griezmann', 'Michel Platini', 'Alan Shearer'], 'correct': 2},

    {'id': 94, 'question': 'Who scored the Golden Goal that won Euro 2000 for France against Italy?',
        'options': ['Thierry Henry', 'David Trezeguet', 'Sylvain Wiltord', 'Zinedine Zidane'], 'correct': 1},

    {'id': 95, 'question': 'Which English player is one of England\'s joint-leading goalscorers in UEFA European Championship history?',
        'options': ['Wayne Rooney', 'Gary Lineker', 'Alan Shearer', 'Michael Owen'], 'correct': 2},

    {'id': 96, 'question': 'Which of these nations has never won the UEFA European Championship?',
        'options': ['Belgium', 'Denmark', 'Greece', 'Portugal'], 'correct': 0},

    {'id': 97, 'question': 'Which nation did Denmark replace at Euro 1992 before going on to win the tournament?',
        'options': ['Soviet Union', 'Czechoslovakia', 'Yugoslavia', 'Romania'], 'correct': 2},

    {'id': 98, 'question': 'In which year did the UEFA European Championship expand from 16 teams to 24 teams?',
        'options': ['2008', '2012', '2016', '2020'], 'correct': 2},

    {'id': 99, 'question': 'Who is the only person to have won the UEFA European Championship as both a player and a manager?',
        'options': ['Franz Beckenbauer', 'Berti Vogts', 'Didier Deschamps', 'Luis Aragones'], 'correct': 1},

    {'id': 100, 'question': 'Who is the all-time top goalscorer in Bundesliga history?',
        'options': ['Robert Lewandowski', 'Klaus Fischer', 'Gerd Muller', 'Jupp Heynckes'], 'correct': 2},

    {'id': 101, 'question': 'Which club has won five Bundesliga titles, making them one of the most successful clubs behind Bayern Munich?',
        'options': ['Hamburg', 'Werder Bremen', 'Borussia Monchengladbach', 'Schalke 04'], 'correct': 2},

    {'id': 102, 'question': 'Who is Germany\'s most-capped international player of all time?',
        'options': ['Miroslav Klose', 'Bastian Schweinsteiger', 'Philipp Lahm', 'Lothar Matthaus'], 'correct': 3},

    {'id': 103, 'question': 'Before Borussia Dortmund, Jurgen Klopp managed which German club?',
        'options': ['Mainz 05', 'Stuttgart', 'Schalke 04', 'Hoffenheim'], 'correct': 0},

    {'id': 104, 'question': 'Who became the youngest head coach in Bundesliga history at 28 years and 205 days old?',
        'options': ['Thomas Tuchel', 'Julian Nagelsmann', 'Marco Rose', 'Domenico Tedesco'], 'correct': 1},

    {'id': 105, 'question': 'Which animal appears on FC Koln\'s club crest?',
        'options': ['A goat', 'A lion', 'An eagle', 'A horse'], 'correct': 0},

    {'id': 106, 'question': 'RB Leipzig are commonly known by which nickname?', 'options': [
        'The Eagles', 'The Red Bulls', 'The Wolves', 'The Miners'], 'correct': 1},

    {'id': 107, 'question': 'How many FIFA World Cups has Germany won as a unified country?',
        'options': ['None', 'Once', 'Twice', 'Four times'], 'correct': 1},

    {'id': 108, 'question': 'Which German club, besides Bayern Munich and Borussia Dortmund, has won the European Cup/Champions League?',
        'options': ['Borussia Monchengladbach', 'Hamburg', 'Werder Bremen', 'Schalke 04'], 'correct': 1},

    {'id': 109, 'question': 'What is the nickname of Borussia Monchengladbach?', 'options': [
        'The Colts', 'The Foals', 'The Stallions', 'The Stallions of the Rhine'], 'correct': 1},

    {'id': 110, 'question': 'Gabriel Batistuta was a native of which South American country?',
        'options': ['Uruguay', 'Argentina', 'Chile', 'Paraguay'], 'correct': 1},

    {'id': 111, 'question': 'In which city does Ajax play their home matches?',
        'options': ['Rotterdam', 'Eindhoven', 'Amsterdam', 'Utrecht'], 'correct': 2},

    {'id': 112, 'question': 'Who defeated the Czech Republic in the final of Euro 1996?',
        'options': ['Germany', 'France', 'Italy', 'Netherlands'], 'correct': 0},

    {'id': 113, 'question': 'How many Italian clubs reached the quarter-finals of the UEFA Cup in the 1999/2000 season?',
        'options': ['0', '1', '2', '3'], 'correct': 0},

    {'id': 114, 'question': 'The Old Firm Derby is contested between Rangers and Celtic, but which city are both clubs based in?',
        'options': ['Edinburgh', 'Belfast', 'Glasgow', 'Dundee'], 'correct': 2},

    {'id': 115, 'question': 'Bray Wanderers, Bohemians, UCD and Kilkenny City are football clubs from which country?',
        'options': ['Northern Ireland', 'Scotland', 'Wales', 'Republic of Ireland'], 'correct': 3},

    {'id': 116, 'question': 'Which German club is known as Die Werkself (The Factory Team)?',
        'options': ['Bayer Leverkusen', 'Eintracht Frankfurt', 'VfL Wolfsburg', 'Hannover 96'], 'correct': 0},    

    {'id': 117, 'question': 'Which country won the first ever UEFA European Championship in 1960?',
        'options': ['Soviet Union', 'Yugoslavia', 'Spain', 'Czechoslovakia'], 'correct': 0},

    {'id': 118, 'question': 'Which nation is second only to Argentina in Copa America titles, with 15 victories?',
        'options': ['Brazil', 'Uruguay', 'Chile', 'Paraguay'], 'correct': 1},

    {'id': 119, 'question': 'Which country has won the most CONCACAF Gold Cup titles?',
        'options': ['United States', 'Canada', 'Mexico', 'Costa Rica'], 'correct': 2},

    {'id': 120, 'question': 'Who has scored the most goals in international football history?',
        'options': ['Lionel Messi', 'Ali Daei', 'Cristiano Ronaldo', 'Ferenc Puskas'], 'correct': 2},

    {'id': 121, 'question': 'Which England player has made the most appearances for the national team?',
        'options': ['Wayne Rooney', 'David Beckham', 'Peter Shilton', 'Steven Gerrard'], 'correct': 2},

    {'id': 122, 'question': 'Which African nation has progressed furthest in FIFA World Cup history?',
        'options': ['Cameroon', 'Senegal', 'Ghana', 'Morocco'], 'correct': 3},

    {'id': 123, 'question': 'Australia defeated which team 31-0 in a 2002 FIFA World Cup qualifier?',
        'options': ['Fiji', 'Tonga', 'American Samoa', 'Cook Islands'], 'correct': 2},

    {'id': 124, 'question': 'Who is the all-time leading goalscorer in Africa Cup of Nations history?',
        'options': ['Didier Drogba', 'Samuel Eto\'o', 'Roger Milla', 'Hossam Hassan'], 'correct': 1},

    {'id': 125, 'question': 'Which nation has won the AFC Asian Cup the most times?',
        'options': ['South Korea', 'Saudi Arabia', 'Iran', 'Japan'], 'correct': 3},

    {'id': 126, 'question': 'Which club has won the UEFA Cup/Europa League the most times?',
        'options': ['Sevilla', 'Liverpool', 'Juventus', 'Inter Milan'], 'correct': 0},

    {'id': 127, 'question': 'Which club ended Paris Saint-Germain\'s dominance by winning Ligue 1 in the 2020/21 season?',
        'options': ['Monaco', 'Lyon', 'Marseille', 'LOSC Lille'], 'correct': 3},

    {'id': 128, 'question': 'Of Cristiano Ronaldo and Lionel Messi, who has won the most La Liga titles?', 'options': [
        'Cristiano Ronaldo', 'Lionel Messi', 'They have won the same number', 'Neither won more than five'], 'correct': 1},

    {'id': 129, 'question': 'Which player shares the record for the most red cards in UEFA Champions League history alongside Edgar Davids and Zlatan Ibrahimovic?',
        'options': ['Pepe', 'Sergio Ramos', 'Patrick Vieira', 'Roy Keane'], 'correct': 1},

    {'id': 130, 'question': 'Which club won the inaugural UEFA Europa Conference League in the 2021/22 season?',
        'options': ['Feyenoord', 'AS Roma', 'West Ham United', 'Leicester City'], 'correct': 1},

    {'id': 131, 'question': 'Which Portuguese club has won the most Primeira Liga titles?',
        'options': ['FC Porto', 'Sporting CP', 'Benfica', 'Braga'], 'correct': 2},
    
    {'id': 132, 'question': 'Which player has received the most yellow cards in Premier League history?',
        'options': ['Lee Bowyer', 'Gareth Barry', 'Roy Keane', 'Mark Noble'], 'correct': 1},

    {'id': 133, 'question': 'Who won the inaugural Premier League Golden Boot in the 1992/93 season?',
        'options': ['Alan Shearer', 'Les Ferdinand', 'Teddy Sheringham', 'Ian Wright'], 'correct': 2},

    {'id': 134, 'question': 'Which of these clubs has never played in the Premier League?',
        'options': ['Oldham Athletic', 'Barnsley', 'Plymouth Argyle', 'Blackpool'], 'correct': 2},

    {'id': 135, 'question': 'Which player has scored the most headed goals in Premier League history?',
        'options': ['Harry Kane', 'Alan Shearer', 'Duncan Ferguson', 'Olivier Giroud'], 'correct': 0},

    {'id': 136, 'question': 'Which manager has won the most Premier League Manager of the Month awards?',
        'options': ['Arsene Wenger', 'Pep Guardiola', 'David Moyes', 'Sir Alex Ferguson'], 'correct': 3},

    {'id': 137, 'question': 'Which Scottish player has scored the most goals in Premier League history?',
        'options': ['Kenny Dalglish', 'Darren Fletcher', 'Duncan Ferguson', 'James McFadden'], 'correct': 2},

    {'id': 138, 'question': 'Who has provided the most assists in Premier League history?',
        'options': ['Cesc Fabregas', 'Wayne Rooney', 'Ryan Giggs', 'Kevin De Bruyne'], 'correct': 2},

    {'id': 139, 'question': 'Which club has won the most Championship play-off finals?',
        'options': ['West Ham United', 'Crystal Palace', 'Watford', 'Leicester City'], 'correct': 1},

    {'id': 140, 'question': 'Which EFL club plays its home matches at St Andrew\'s?', 'options': [
        'Coventry City', 'Birmingham City', 'West Bromwich Albion', 'Stoke City'], 'correct': 1},

    {'id': 141, 'question': 'Which club has won the EFL Trophy the most times?', 'options': [
        'Bristol City', 'Blackpool', 'Wigan Athletic', 'Peterborough United'], 'correct': 0},

    {'id': 142, 'question': 'How many clubs compete across the Championship, League One and League Two?',
        'options': ['60', '66', '72', '78'], 'correct': 2},

    {'id': 143, 'question': 'The Bantams is the nickname of which EFL club?', 'options': [
        'Barnsley', 'Bradford City', 'Burton Albion', 'Bristol Rovers'], 'correct': 1},

    {'id': 144, 'question': 'Which club set the Championship record with 106 points in the 2005/06 season?',
        'options': ['Sunderland', 'Reading', 'Burnley', 'Wolverhampton Wanderers'], 'correct': 1},

    {'id': 145, 'question': 'When Bradford City reached the 2013 League Cup final, which division were they playing in?',
        'options': ['Championship', 'League One', 'League Two', 'National League'], 'correct': 2},

    {'id': 146, 'question': 'Which striker scored a record 43 goals in the Championship during the 2021/22 season?',
        'options': ['Ivan Toney', 'Aleksandar Mitrovic', 'Teemu Pukki', 'Ollie Watkins'], 'correct': 1},

    {'id': 147, 'question': 'Luton Town play their home matches at which stadium?', 'options': [
        'The Den', 'Kenilworth Road', 'Loftus Road', 'Bloomfield Road'], 'correct': 1},

    {'id': 148, 'question': 'Who was the first British player to move abroad to play professional football?',
        'options': ['John Charles', 'Denis Law', 'Jimmy Greaves', 'Tom Finney'], 'correct': 0},

    {'id': 149, 'question': 'Kevin Keegan won two Ballon d\'Or awards while playing for which German club?',
        'options': ['Bayern Munich', 'Borussia Monchengladbach', 'Hamburg', 'Cologne'], 'correct': 2},

    {'id': 150, 'question': 'Paul Lambert won the 1996/97 UEFA Champions League with which club?',
        'options': ['Bayern Munich', 'Borussia Dortmund', 'Celtic', 'Juventus'], 'correct': 1},

    {'id': 151, 'question': 'How much did Real Madrid pay to sign Jude Bellingham in 2023?',
        'options': ['£81 million', '£88.5 million', '£104 million', '£95 million'], 'correct': 1},

    {'id': 152, 'question': 'Paul Gascoigne left Tottenham Hotspur in 1992 to join which Italian club?',
        'options': ['Juventus', 'AC Milan', 'Lazio', 'Roma'], 'correct': 2},

    {'id': 153, 'question': 'How many UEFA Champions League titles did Gareth Bale win with Real Madrid?',
        'options': ['Three', 'Four', 'Five', 'Six'], 'correct': 2},

    {'id': 154, 'question': 'In which Asian country did Gary Lineker finish his playing career?',
        'options': ['South Korea', 'China', 'Japan', 'Thailand'], 'correct': 2},

    {'id': 155, 'question': 'Steven Gerrard played for Liverpool and which foreign club during his professional career?',
        'options': ['LA Galaxy', 'New York City FC', 'LAFC', 'Inter Miami'], 'correct': 0},

    {'id': 156, 'question': 'David Beckham played for Manchester United and which English club during his career?',
        'options': ['Preston North End', 'Leeds United', 'Birmingham City', 'Nottingham Forest'], 'correct': 0},

    {'id': 157, 'question': 'George Best played for how many different clubs in the United States?',
        'options': ['Two', 'Three', 'Four', 'Five'], 'correct': 1},

    {'id': 158, 'question': 'How much did Paris Saint-Germain pay to sign Neymar from Barcelona in 2017?',
        'options': ['€180 million', '€200 million', '€222 million', '€250 million'], 'correct': 2},

    {'id': 159, 'question': 'Which £80 million signing became the world\'s most expensive defender in 2019?',
        'options': ['Virgil van Dijk', 'Harry Maguire', 'Matthijs de Ligt', 'Ruben Dias'], 'correct': 1},

    {'id': 160, 'question': 'Who was the first British footballer to cost £1 million?', 'options': [
        'Kevin Keegan', 'Trevor Francis', 'Bryan Robson', 'Kenny Dalglish'], 'correct': 1},

    {'id': 161, 'question': 'Who is the most expensive goalkeeper in football history?', 'options': [
        'Alisson Becker', 'Gianluigi Buffon', 'Kepa Arrizabalaga', 'Andre Onana'], 'correct': 2},

    {'id': 162, 'question': 'Who was the first footballer to command a transfer fee of over £50 million?',
        'options': ['Cristiano Ronaldo', 'Luis Figo', 'Zinedine Zidane', 'Kaka'], 'correct': 3},

    {'id': 163, 'question': 'Who is the most expensive African footballer of all time?', 'options': [
        'Victor Osimhen', 'Riyad Mahrez', 'Nicolas Pepe', 'Mohamed Salah'], 'correct': 2},

    {'id': 164, 'question': 'Who became the first women\'s footballer to command a transfer fee of £1 million in 2025?',
        'options': ['Sam Kerr', 'Olivia Smith', 'Lauren James', 'Aitana Bonmati'], 'correct': 1},

    {'id': 165, 'question': 'How many transfers worth more than €70 million has Romelu Lukaku been involved in?',
        'options': ['Two', 'Three', 'Four', 'Five'], 'correct': 1},

    {'id': 166, 'question': 'Which non-European club ranks in the top 10 for spending in a single summer transfer window?',
        'options': ['Al Nassr', 'Inter Miami', 'Al Hilal', 'Flamengo'], 'correct': 2},

    {'id': 167, 'question': 'Real Madrid broke the world transfer record in 2001 by signing which player from Juventus?',
        'options': ['Pavel Nedved', 'Zinedine Zidane', 'Edgar Davids', 'David Trezeguet'], 'correct': 1},

    {'id': 168, 'question': 'In which year was the inaugural Major League Soccer season played?',
        'options': ['1994', '1995', '1996', '1998'], 'correct': 2},

    {'id': 169, 'question': 'What is the name of the trophy awarded to the team with the best regular-season record in MLS?',
        'options': ['MLS Cup', 'Commissioner\'s Trophy', 'Supporters\' Shield', 'Founders Cup'], 'correct': 2},

    {'id': 170, 'question': 'Who is Major League Soccer\'s all-time leading goalscorer?',
        'options': ['Landon Donovan', 'Chris Wondolowski', 'Josef Martinez', 'Bradley Wright-Phillips'], 'correct': 1},

    {'id': 171, 'question': 'Which former Barcelona player joined Lionel Messi at Inter Miami in 2023?',
        'options': ['Sergio Busquets', 'Gerard Pique', 'Andres Iniesta', 'Dani Alves'], 'correct': 0},

    {'id': 172, 'question': 'Which club competes in the Cascadia Cup?', 'options': [
        'LA Galaxy', 'Seattle Sounders', 'Real Salt Lake', 'Minnesota United'], 'correct': 1},

    {'id': 173, 'question': 'Which Italian playmaker scored an MLS-record 13 free-kick goals for Toronto FC between 2015 and 2018?',
        'options': ['Andrea Pirlo', 'Sebastian Giovinco', 'Alessandro Del Piero', 'Marco Verratti'], 'correct': 1},

    {'id': 174, 'question': 'Which MLS club plays its home matches at Sports Illustrated Stadium?', 'options': [
        'New York City FC', 'New York Red Bulls', 'Philadelphia Union', 'DC United'], 'correct': 1},

    {'id': 175, 'question': 'What is the official term used to describe the process by which a new team joins Major League Soccer?',
        'options': ['Expansion', 'Admission', 'Promotion', 'Franchising'], 'correct': 0},

    {'id': 176, 'question': 'Sporting Kansas City was known by what name between 1997 and 2010?', 'options': [
        'Kansas City United', 'Kansas City Wizards', 'Missouri Wizards', 'Sporting Missouri'], 'correct': 1},

    {'id': 177, 'question': 'Which player, once dubbed "the next Pele", was selected first overall in the 2004 MLS SuperDraft?',
        'options': ['Clint Dempsey', 'Jozy Altidore', 'Freddy Adu', 'Michael Bradley'], 'correct': 2},

    {'id': 178, 'question': 'Which of these clubs has won Ligue 1?',
        'options': ['Auxerre', 'Toulouse', 'Metz', 'Cannes'], 'correct': 0},

    {'id': 179, 'question': 'Which is the oldest football club in France?',
        'options': ['Le Havre', 'Metz', 'Strasbourg', 'Lille'], 'correct': 0},

    {'id': 180, 'question': 'Which French club was the first to reach a European Cup/Champions League final?',
        'options': ['Reims', 'Marseille', 'Saint-Etienne', 'Monaco'], 'correct': 0},

    {'id': 181, 'question': 'How many consecutive Ligue 1 titles did Lyon win during the 2000s?',
        'options': ['5', '6', '7', '8'], 'correct': 2},

    {'id': 182, 'question': 'Which manager is the only person to have won both the UEFA European Championship and the Africa Cup of Nations?',
        'options': ['Jacques Santini', 'Claude Le Roy', 'Roger Lemerre', 'Herve Renard'], 'correct': 2},

    {'id': 183, 'question': 'After Paris Saint-Germain, which club has won the second-most Ligue 1 titles?',
        'options': ['Marseille', 'Lyon', 'Monaco', 'Saint-Etienne'], 'correct': 3},

    {'id': 184, 'question': 'Aime Jacquet guided France to World Cup glory in 1998, but which club did he manage to a Ligue 1 title?',
        'options': ['Saint-Etienne', 'Bordeaux', 'Nantes', 'Lille'], 'correct': 1},

    {'id': 185, 'question': 'Which of these clubs has never won Ligue 1?',
        'options': ['Rennes', 'Lens', 'Nice', 'Sochaux'], 'correct': 0},

    {'id': 186, 'question': 'Jules Rimet, the man behind the creation of the FIFA World Cup, founded which football club?',
        'options': ['Red Star', 'Metz', 'Amiens', 'Valenciennes'], 'correct': 0},

    {'id': 187, 'question': 'Which manager is the only person to have won the Africa Cup of Nations with two different countries?',
        'options': ['Bruno Metsu', 'Philippe Troussier', 'Roger Lemerre', 'Herve Renard'], 'correct': 3},

    {'id': 188, 'question': 'Which club has spent the most seasons in the French top flight?',
        'options': ['Monaco', 'Bordeaux', 'Lyon', 'Marseille'], 'correct': 3},

    {'id': 189, 'question': 'Which manager has won the most Ligue 1 titles?', 'options': [
        'Aime Jacquet', 'Guy Roux', 'Gerard Houllier', 'Albert Batteux'], 'correct': 3},

    {'id': 190, 'question': 'With which club did Arsene Wenger win Ligue 1 as a player?',
        'options': ['Monaco', 'Strasbourg', 'Saint-Etienne', 'Bordeaux'], 'correct': 1},

    {'id': 191, 'question': 'The all-time top scorer in Ligue 1 history was born in which country?',
        'options': ['France', 'Sweden', 'Argentina', 'Brazil'], 'correct': 2},

    {'id': 192, 'question': 'Which French player is correctly matched to his family heritage?', 'options': [
        'Zinedine Zidane - Tunisia', 'Blaise Matuidi - Cameroon', 'Paul Pogba - Senegal', 'Ngolo Kante - Mali'], 'correct': 3},

    {'id': 193, 'question': 'Which manager guided Paris Saint-Germain to their first Ligue 1 title?',
        'options': ['Arsene Wenger', 'Artur Jorge', 'Georges Peyroche', 'Gerard Houllier'], 'correct': 3},

    {'id': 194, 'question': 'Which pair of players were NOT teammates at club level?', 'options': [
        'Claude Puel & Youri Djorkaeff', 'Arsene Wenger & Raymond Domenech', 'Zinedine Zidane & Didier Deschamps', 'Nicolas Anelka & Robert Pires'], 'correct': 3},

    {'id': 195, 'question': 'Which player has won the most Ligue 1 Top Goalscorer awards?', 'options': [
        'Jean-Pierre Papin', 'Kylian Mbappe', 'Delio Onnis', 'Carlos Bianchi'], 'correct': 1},

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
        self.host_id = None
        self.rematch_votes = {}
        self.is_sudden_death = False
        self.sudden_death_answers = {}
        self.sudden_death_started_at = None

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
        self.rematch_votes = {}
        self.is_sudden_death = False
        self.sudden_death_answers = {}
        self.sudden_death_started_at = None

        for player in self.players.values():
            player['score'] = 0
            player['current_answer'] = None
            player['answers'] = []
            player['is_ready'] = False

    def get_player_statuses(self):
        """Return player names and ready statuses for the waiting room."""
        return [
            {'id': player['id'], 'name': player['name'], 'is_ready': player['is_ready']}
            for player in self.players.values()
        ]

    def get_rematch_statuses(self):
        """Return each player's rematch vote status."""
        return [
            {
                'id': player['id'],
                'name': player['name'],
                'wants_rematch': self.rematch_votes.get(player['id'], False),
            }
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
        """Mark answers, update scores, and return each player's result."""
        question = self.selected_questions[self.current_question_index]
        results = {}

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

            results[player['id']] = {
                'is_correct': is_correct,
                'selected': selected_answer,
                'correct': question['correct'],
            }

            player['current_answer'] = None

        return results

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
    room.host_sid = request.sid
    join_room(room_code)

    emit('room_created', {
        'room_code': room_code,
        'players': room.get_player_statuses(),
        'is_host': True
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
        'players': room.get_player_statuses(),
        'is_host': False
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


def get_sudden_death_times(room):
    """Return readable sudden death answer times for the final screen."""
    times = []

    for player_id, answer_data in room.sudden_death_answers.items():
        player = room.players.get(player_id)

        if not player:
            continue

        answer_time = answer_data.get('answer_time')

        times.append({
            'name': player['name'],
            'is_correct': answer_data.get('is_correct', False),
            'answer_time': round(answer_time, 2) if answer_time is not None else None,
            'timed_out': answer_data.get('timed_out', False),
        })

    return sorted(
        times,
        key=lambda item: item['answer_time'] if item['answer_time'] is not None else 999
    )


def emit_sudden_death_result_after_delay(room_code, winner_id):
    """Give players time to see correct/wrong feedback before showing final result."""
    time.sleep(1.5)

    room = rooms.get(room_code)

    if not room:
        return

    winner = room.players[winner_id]

    final_scores = {
        player['name']: player['score']
        for player in room.players.values()
    }

    socketio.emit('game_ended', {
        'final_scores': final_scores,
        'winner': {
            'name': winner['name'],
            'score': winner['score'],
            'won_by_sudden_death': True,
            'sudden_death_times': get_sudden_death_times(room),
        },
    }, to=room_code)

def end_sudden_death(room_code, winner_id):
    """End sudden death and declare the fastest correct player as winner."""
    room = rooms.get(room_code)

    if not room or room.game_ended:
        return

    room.game_ended = True
    room.is_sudden_death = False

    socketio.start_background_task(
        emit_sudden_death_result_after_delay,
        room_code,
        winner_id
    )


def emit_sudden_death_draw_after_delay(room_code):
    """Give players time to see wrong feedback before showing draw result."""
    time.sleep(1.5)

    room = rooms.get(room_code)

    if not room:
        return

    final_scores = {
        player['name']: player['score']
        for player in room.players.values()
    }

    socketio.emit('game_ended', {
        'final_scores': final_scores,
        'winner': {
            'name': 'Draw',
            'score': max(final_scores.values()) if final_scores else 0,
            'won_by_sudden_death': False,
            'sudden_death_draw': True,
            'sudden_death_times': get_sudden_death_times(room),
        },
    }, to=room_code)


def end_sudden_death_draw(room_code):
    """End sudden death as a draw."""
    room = rooms.get(room_code)

    if not room or room.game_ended:
        return

    room.game_ended = True
    room.is_sudden_death = False

    socketio.start_background_task(
        emit_sudden_death_draw_after_delay,
        room_code
    )

def handle_sudden_death_answer(room_code, room, player_id, answer_index):
    """Handle sudden death answers where fastest correct answer wins."""
    if player_id in room.sudden_death_answers:
        return

    question = room.selected_questions[room.current_question_index]
    is_correct = answer_index == question['correct']

    answered_at = time.time()


    answer_time = (
        answered_at - room.sudden_death_started_at
        if room.sudden_death_started_at
        else None
    )

    room.sudden_death_answers[player_id] = {
        'selected': answer_index,
        'is_correct': is_correct,
        'answered_at': answered_at,
        'answer_time': answer_time,
    }

    socketio.emit('answer_result', {
        'results': {
            player_id: {
                'is_correct': is_correct,
                'selected': answer_index,
                'correct': question['correct'],
            }
        }
    }, to=player_id)

    decide_sudden_death(room_code)

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
    
    if room.is_sudden_death:
        handle_sudden_death_answer(room_code, room, sid, answer_index)
        return

    room.submit_answer(sid, answer_index)

    if room.have_all_players_answered() and not room.is_evaluating:
        room.is_evaluating = True
        if room.question_timeout:
            room.question_timeout.cancel()
        socketio.start_background_task(evaluate_after_short_delay, room_code)


@socketio.on('request_rematch')
def handle_request_rematch():
    """Handle a player's rematch vote."""
    sid = request.sid
    room_code, room = get_room_for_player(sid)

    if not room or not room.game_ended:
        return

    room.rematch_votes[sid] = True

    socketio.emit('rematch_updated', {
        'players': room.get_rematch_statuses(),
    }, to=room_code)

    if len(room.players) == 2 and all(
        room.rematch_votes.get(player_id, False)
        for player_id in room.players
    ):
        room.game_started = False
        room.game_ended = False
        room.current_question_index = 0
        room.selected_questions = []
        room.is_evaluating = False
        room.rematch_votes = {}

        for player in room.players.values():
            player['score'] = 0
            player['current_answer'] = None
            player['answers'] = []
            player['is_ready'] = False

        socketio.emit('rematch_ready', {
            'room_code': room_code,
            'players': room.get_player_statuses(),
        }, to=room_code)

def evaluate_after_short_delay(room_code):
    """Briefly show answer-submitted feedback before moving on."""
    time.sleep(0.5)
    evaluate_and_next_question(room_code)


def is_game_tied(room):
    """Return True when both players have the same score."""
    scores = [player['score'] for player in room.players.values()]
    return len(scores) == 2 and scores[0] == scores[1]


def decide_sudden_death(room_code):
    """Decide sudden death once both players have answered or timed out."""
    room = rooms.get(room_code)

    if not room or room.game_ended:
        return

    if len(room.sudden_death_answers) < len(room.players):
        return

    if room.question_timeout:
        room.question_timeout.cancel()
        room.question_timeout = None

    correct_answers = [
        {
            'player_id': answer_player_id,
            'answered_at': answer_data['answered_at'],
        }
        for answer_player_id, answer_data in room.sudden_death_answers.items()
        if answer_data['is_correct']
    ]

    if len(correct_answers) == 0:
        end_sudden_death_draw(room_code)
        return

    if len(correct_answers) == 1:
        end_sudden_death(room_code, winner_id=correct_answers[0]['player_id'])
        return

    correct_answers.sort(key=lambda answer: answer['answered_at'])

    first_answer = correct_answers[0]
    second_answer = correct_answers[1]

    if first_answer['answered_at'] == second_answer['answered_at']:
        end_sudden_death_draw(room_code)
    else:
        end_sudden_death(room_code, winner_id=first_answer['player_id'])

def evaluate_sudden_death_timeout(room_code):
    """Force sudden death to finish after 5 seconds."""
    room = rooms.get(room_code)

    if not room or room.game_ended or not room.is_sudden_death:
        return

    question = room.selected_questions[room.current_question_index]

    for player_id, player in room.players.items():
        if player_id not in room.sudden_death_answers:
            room.sudden_death_answers[player_id] = {
                'selected': None,
                'is_correct': False,
                'answered_at': None,
                'answer_time': None,
                'timed_out': True,
            }

            socketio.emit('answer_result', {
                'results': {
                    player_id: {
                        'is_correct': False,
                        'selected': None,
                        'correct': question['correct'],
                        'timed_out': True,
                    }
                }
            }, to=player_id)

    decide_sudden_death(room_code)

def start_sudden_death_delayed(room_code):
    """Wait briefly before showing the sudden death question."""
    time.sleep(3)

    room = rooms.get(room_code)

    if not room or room.game_ended:
        return
    
    room.sudden_death_started_at = time.time()

    
    socketio.emit('sudden_death_question', {
        'question': room.get_question_data(),
        'scores': room.get_scores(),
    }, to=room_code)


    room.question_timeout = threading.Timer(
        5.0,
        evaluate_sudden_death_timeout,
        args=[room_code]
    )
    room.question_timeout.start()

def start_sudden_death(room_code):
    """Start a sudden death tie-break question."""
    room = rooms.get(room_code)

    if not room or room.game_ended:
        return

    room.is_sudden_death = True
    room.sudden_death_answers = {}
    room.current_question_index = 0
    room.selected_questions = random.sample(QUESTIONS, 1)

    for player in room.players.values():
        player['current_answer'] = None

    socketio.emit('sudden_death_starting', {
        'message': 'Sudden death! Fastest correct answer wins!'
    }, to=room_code)

    socketio.start_background_task(start_sudden_death_delayed, room_code)

def evaluate_and_next_question(room_code):
    """Evaluate current answers, then either send next question or end the game."""
    room = rooms.get(room_code)
    if not room or room.game_ended:
        return

    if room.question_timeout:
        room.question_timeout.cancel()
        room.question_timeout = None

    results = room.evaluate_answers()


    room.is_evaluating = False

    socketio.emit('answer_result', {
        'results': results,
    }, to=room_code)

    time.sleep(1.2)

    if room.move_to_next_question():
        socketio.emit('question_answered', {
            'question': room.get_question_data(),
            'question_number': room.current_question_index + 1,
            'total_questions': len(room.selected_questions),
            'scores': room.get_scores(),
        }, to=room_code)
        schedule_question_timeout(room_code)
    else:
        if is_game_tied(room):
            start_sudden_death(room_code)
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


@socketio.on('close_room')
def close_room():
    for room_code, room in rooms.items():

        if room.host_sid == request.sid:

            socketio.emit(
                'room_closed',
                {
                    'message': 'The host closed the room.'
                },
                room=room_code
            )

            del rooms[room_code]

            break

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
