from flask import Flask, make_response, request, redirect, url_for, render_template
from os import urandom
from binascii import hexlify
from random import choice, shuffle
from time import time, strftime
from threading import Thread
from hashlib import sha512
import json
import sqlite3
import requests

app = Flask(__name__)
STATISTICS = {"Players": 0, "Completions": 0, "Tamper Attempts": 0,
              "Finishers": [], "Highscore": ["None", 1024], "Tamperers": []}
TO = "test@test.com"
FROM = "Game Info <test@test.com>"
MG_APIKEY = "key"
GH_API = "username:key"
GH_ID = "id"
POSSIBLE_COMPLETED = 4
ADDRESS = "127.0.0.1"
PORT = 5000
DEBUG = True
TESTING = False
DEV = ""
DATABASE = "data.db"
DOMAIN = "test.com"
TIME = 900


# Name: Finishers
# Purpose: access finishers table in data.db
class Finishers(object):
    # Name: query
    # Purpose: query the table based off of inputs
    # Inputs: uid as string
    # Outputs: list of returned objects
    @staticmethod
    def query(uid):
        # Connect to database
        connection = sqlite3.connect(DATABASE)

        # Get data
        data = connection.execute("SELECT * FROM finishers WHERE id = ?", [uid]).fetchone()
        if not data:
            data = None

        # Close and return data
        connection.close()
        return data

    # Name: insert
    # Purpose: insert a row into the table
    # Inputs: uid as string, name as string, email as string, total_time as integer
    # Outputs:
    @staticmethod
    def insert(uid, name, email, total_time):
        # Connect to database
        connection = sqlite3.connect(DATABASE)

        # Insert into table
        connection.execute("INSERT INTO finishers VALUES (?, ?, ?, ?)", [uid, name, total_time, email])

        # Close connection
        connection.commit()
        connection.close()


# Name: Puzzles
# Purpose: access puzzles table in data.db
class Puzzles(object):
    # Name: query
    # Purpose: query the table based off of inputs
    # Inputs: pid as string
    # Outputs: list of returned lists
    @staticmethod
    def query(pid):
        # Connect to database
        connection = sqlite3.connect(DATABASE)

        # Get data
        data = connection.execute("SELECT * FROM puzzles WHERE id = ?", [pid]).fetchall()

        # Close and return data
        connection.close()
        return data

    # Name: update
    # Purpose: update a row in the table
    # Inputs: pid as string
    # Outputs:
    @staticmethod
    def update(pid):
        # Connect to database
        connection = sqlite3.connect(DATABASE)

        # Update completions
        prev = connection.execute("SELECT completions FROM puzzles WHERE id = ?", [pid]).fetchone()
        if not prev:
            return
        else:
            prev = prev[0]
        connection.execute("UPDATE puzzles SET completions = ? WHERE id = ?", [prev + 1, pid])

        # Close and commit
        connection.commit()
        connection.close()

    # Name: solution
    # Purpose: get solution for given puzzle
    # Inputs: pid as string
    # Outputs: solution as string
    @staticmethod
    def solution(pid):
        # Connect to database
        connection = sqlite3.connect(DATABASE)

        # Get solution from table
        sol = connection.execute("SELECT solution FROM puzzles WHERE id = ?", [pid]).fetchone()
        if not sol:
            sol = None
        else:
            sol = sol[0]

        # Close connection & return data
        connection.close()
        return sol

    # Name: data
    # Purpose: get data for specific puzzle
    # Inputs: pid as string
    # Outputs: tuple of title and prompt
    @staticmethod
    def data(pid):
        # Connect to database
        connection = sqlite3.connect(DATABASE)

        # Get html for given puzzle id
        data = connection.execute("SELECT title, prompt FROM puzzles WHERE id = ?", [pid]).fetchone()
        if not data:
            data = None

        # Close and return data
        connection.close()
        return data

    # Name: set
    # Purpose: get random set of puzzles
    # Inputs:
    # Outputs: list of puzzle ids
    @staticmethod
    def set():
        # Connect to database
        connection = sqlite3.connect(DATABASE)

        # Get all ids
        pids = []
        for pid in connection.execute("SELECT id FROM puzzles").fetchall():
            pids.append(pid[0])

        # Close connection
        connection.close()

        # Get num ids
        selected = []
        for i in range(POSSIBLE_COMPLETED):
            shuffle(pids)
            c = choice(pids)
            # Check not already chosen
            while c in selected:
                c = choice(pids)
            selected.append(c)

        # Return selected ids
        return selected


# Name: UserData
# Purpose: access user_data table in data.db
class UserData(object):
    # Name: query
    # Purpose: query the table based off of inputs
    # Inputs: uid as string
    # Outputs: list of returned objects
    @staticmethod
    def query(uid):
        # Connect to database
        connection = sqlite3.connect(DATABASE)

        # Get user
        user = connection.execute("SELECT * FROM user_data WHERE id = ?", [uid]).fetchone()

        # Close and return user
        connection.close()
        return user

    # Name: insert
    # Purpose: insert a row into the table
    # Inputs: uid as string, pages as string, current as string time_start as integer
    # Outputs:
    @staticmethod
    def insert(uid, pages, current, time_start):
        # Connect to database
        connection = sqlite3.connect(DATABASE)

        # Insert into table
        connection.execute("INSERT INTO user_data (id, pages, current, start) VALUES (?, ?, ?, ?)",
                           (uid, pages, current, time_start))

        # Commit and close connection
        connection.commit()
        connection.close()

    # Name: update
    # Purpose: update a row in the table
    # Inputs: uid as string, complete as integer (default: None), time_end as integer (default: None),
    #           tampered as boolean (default: None), current as string (default: None)
    # Outputs:
    @staticmethod
    def update(uid, complete=None, time_end=None, tampered=None, current=None):
        # Check if user exists
        if len(UserData.query(uid)) == 0:
            return

        # Set to previous value if not passed
        if not complete:
            complete = UserData.query(uid)[3]
        if not time_end:
            time_end = UserData.query(uid)[5]
        if not tampered:
            tampered = UserData.query(uid)[6]
        if not current:
            current = UserData.query(uid)[2]

        # Connect to database
        connection = sqlite3.connect(DATABASE)

        # Update row
        connection.execute("UPDATE user_data SET complete = ?, end = ?, tampered = ?, current = ? WHERE id = ?",
                           [complete, time_end, tampered, current, uid])

        # Commit and close connection
        connection.commit()
        connection.close()


# Name: Send
# Purpose: send emails to specified address
class Send(object):
    # Name: stats
    # Purpose: send the game statistics
    # Inputs:
    # Outputs: dict
    @staticmethod
    def stats():
        # Format finishers
        finishers = "# Finishers\n###### Updated On: " + strftime("%m-%d-%Y %H:%M:%S") + "\n\n"
        for i, finisher in enumerate(STATISTICS["Finishers"]):
            finishers += "Player " + str(i + 1) + ":\n"
            finishers += "* Name: " + finisher["name"] + "\n"
            finishers += "* Email: " + finisher["email"] + "\n"
            finishers += "* Time: " + str(finisher["time"]) + " seconds\n\n"

        # Format tamperers
        tamperers = "# Tamperers\n###### Updated On: " + strftime("%m-%d-%Y %H:%M:%S") + "\n\n"
        for i, tamperer in enumerate(STATISTICS["Tamperers"]):
            tamperers += "Tamperer " + str(i + 1) + ":\n"
            tamperers += "* Name: " + tamperer["name"] + "\n"
            tamperers += "* Email: " + tamperer["email"] + "\n\n"

        generic = "# Generic Stats\n###### Updated on: " + strftime("%m-%d-%Y %H:%M:%S") + \
            "\n\nTotal Players: " + str(STATISTICS["Players"]) + \
            "\n\nTotal Completions: " + str(STATISTICS["Completions"]) + \
            "\n\nAttempted Tampers: " + str(STATISTICS["Tamper Attempts"]) + \
            "\n\nHighscore Holder:\n* Name: " + STATISTICS["Highscore"][0] + \
            "\n* Time: " + str(STATISTICS["Highscore"][1]) + " seconds\n"

        data = {
            "description": "Krantz's Challenge Play Statistics",
            "files": {
                "generic.md": {
                    "content": generic
                },
                "finishers.md": {
                    "content": finishers
                },
                "tamperers.md": {
                    "content": tamperers
                }
            }
        }

        return data

    # Name: finisher
    # Purpose: send stats of new finisher
    # Inputs: hs as boolean
    # Outputs: status code
    @staticmethod
    def finisher(player, hs=False):
        # Get puzzles
        puzzles = ""
        for i, p in enumerate(json.loads(player[1])):
            puzzles += "\t\t" + str(i + 1) + ": " + p + "\n"

        body = "New Finisher on " + strftime("%m-%d-%Y %H:%M:%S") + \
            ":\n\tName: " + STATISTICS["Finishers"][len(STATISTICS["Finishers"]) - 1]["name"] + ",\n" + \
            "\tEmail: " + STATISTICS["Finishers"][len(STATISTICS["Finishers"]) - 1]["email"] + ",\n" + \
            "\tTime: " + str(STATISTICS["Finishers"][len(STATISTICS["Finishers"]) - 1]["time"]) + " seconds\n" + \
            "\tAssigned Puzzles: " + puzzles

        if hs:
            body += "New Highscore! Contact them & give them their reward."

        a = ("api", MG_APIKEY)
        d = {"from": FROM,
             "to": TO,
             "subject": "Krantz's Challenge: New Finisher",
             "text": body
             }
        return requests.post("https://api.mailgun.net/v3/" + DOMAIN + "/messages", auth=a, data=d)

    # Name: tamperer
    # Purpose: send stats of new tamperer
    # Inputs:
    # Outputs: status code
    @staticmethod
    def tamperer():
        body = "New Tamperer on " + strftime("%m-%d-%Y %H:%M:%S") + \
            ":\n\tName: " + STATISTICS["Tamperers"][len(STATISTICS["Tamperers"]) - 1]["name"] + ",\n" + \
            "\tEmail: " + STATISTICS["Tamperers"][len(STATISTICS["Tamperers"]) - 1]["email"] + ",\n" + \
            "Contact this person to find out the bug."
        a = ("api", MG_APIKEY)
        d = {"from": FROM,
             "to": TO,
             "subject": "Krantz's Challenge: New Tamperer",
             "text": body
             }
        return requests.post("https://api.mailgun.net/v3/" + DOMAIN + "/messages", auth=a, data=d)


# Name: Reporter
# Purpose: report game statistics to secret gist
class Reporter(Thread):
    # Name: __init__
    # Purpose: initialize values
    # Inputs:
    # Outputs
    def __init__(self):
        self.exec = time() + TIME
        self.exit = False
        super().__init__()

    # Name: run
    # Purpose: run reporting loop
    # Inputs:
    # Outputs:
    def run(self):
        while True:
            if self.exec == time():
                print("Ran")
                requests.patch("https://api.github.com/gists/" + GH_ID, json=Send.stats(), auth=tuple(GH_API.split(":")))
                self.exec = time() + TIME
            if self.exit:
                break

    # Name: stop
    # Purpose: stop reporting loop
    # Inputs:
    # Outputs
    def stop(self):
        self.exit = True


# Name: get_data_from_cookie
# Purpose: get the data from the data cookie
# Inputs:
# Outputs: list w/ all data
def get_data_from_cookie():
    # Get and decode data in cookie
    cookie = request.cookies.get("data").split(".")
    # Return cookie list
    return cookie


# Name: verify_data
# Purpose: check if all data checks out
# Inputs: cookie as list
# Outputs: boolean
def verify_data(cookie):
    # Verify uid not tampered w/
    if sha512(cookie[0].encode()).hexdigest() != cookie[1]:
        return False

    # Verify uid matches on in database
    if not UserData.query(cookie[0]):
        return False

    # If no error, return true
    return True


# Name: create_user
# Purpose: create a users data
# Inputs:
# Outputs: jwt string
def create_user():
    # Create id and default data
    uid = hexlify(urandom(16)).decode()

    # Give user random set of 4 puzzles
    pids = Puzzles.set()

    # Set start time
    time_start = int(time())

    # Set current puzzle to first puzzle in pages list
    c_pid = pids[0]

    # Save to database
    UserData.insert(uid, json.dumps(pids), c_pid, time_start)

    # Return string to go in cookie
    return uid + "." + sha512(uid.encode()).hexdigest()


# Name: index
# Purpose: listen for get requests, redirect to home
# Inputs:
# Outputs: redirect
@app.route("/")
def index():
    return redirect(url_for("home"))


# Name: home
# Purpose: listen for get requests, render main page
# Inputs:
# Outputs: rendered html
@app.route("/home")
def home():
    return render_template("index" + DEV + ".html", name=STATISTICS["Highscore"][0], time=STATISTICS["Highscore"][1])


# Name: start
# Purpose: listen for get requests, begin user's challenge
# Inputs:
# Outputs: redirect to starting page
@app.route("/start")
def start():
    # Check user has not started
    if request.cookies.get("data"):
        # Get cookie data
        cookie = get_data_from_cookie()

        # Check if tampered
        if not verify_data(cookie):
            # Update tamper statistics
            STATISTICS["Tamper Attempts"] += 1

            resp = make_response(render_template("tamperer" + DEV + ".html"))
            # Remove data cookie
            resp.set_cookie("data", "", expires=0)
            return resp

        # Redirect to puzzle working on
        return redirect(url_for("puzzle"))

    # Update statistics
    STATISTICS["Players"] += 1

    # Create response w/ cookie
    resp = make_response(redirect(url_for("puzzle")))
    resp.set_cookie("data", create_user(), expires=(time() + 316000000))
    return resp


# Name: finish
# Purpose: listen for get & post requests, finish user's challenge
# Inputs:
# Outputs: redirects
@app.route("/finish", methods=["GET", "POST"])
def finish():
    # Check user has started
    if not request.cookies.get("data"):
        return render_template("tamperer" + DEV + ".html")

    # Get cookie data
    cookie = get_data_from_cookie()
    played = request.cookies.get("pstatus")

    # Validate data
    if not verify_data(cookie):
        # Update tamper statistics
        STATISTICS["Tamper Attempts"] += 1

        # Remove data cookie
        resp = make_response(render_template("tamperer" + DEV + ".html"))
        resp.set_cookie("data", "", expires=0)
        return resp

    if request.method == "GET":
        c = Finishers.query(cookie[0])
        u = UserData.query(cookie[0])
        if u[3] != 4:
            return redirect(url_for("puzzle"))

        if c:
            return render_template("finish" + DEV + ".html", name=c[1], time=c[2])

        return render_template("pre-finish" + DEV + ".html")

    # Get form data
    name = request.form.get("name")
    email = request.form.get("email")

    # Insert into finishers database
    player = UserData.query(cookie[0])
    if player[6] != 1:
        Finishers.insert(cookie[0], name, email, (player[5] - player[4]))

    # Update completions & finishers
    STATISTICS["Completions"] += 1
    STATISTICS["Finishers"].append({"name": name, "email": email, "time": (player[5] - player[4])})

    # Check if user got highscore
    prev = None
    if STATISTICS["Highscore"][1] > (player[5]-player[4]):
        prev = STATISTICS["Highscore"]
        STATISTICS["Highscore"] = [name, (player[5]-player[4])]

    # Check if tampered
    if player[6] == 1:
        # Remove from completions,finishers,highscore & add to tamperers
        STATISTICS["Completions"] -= 1
        STATISTICS["Tamperers"].append(STATISTICS["Finishers"].pop(len(STATISTICS["Finishers"]) - 1))
        if STATISTICS["Highscore"][0] == name:
            STATISTICS["Highscore"] = prev

        # Notify new Tamperer
        Send.tamperer()

        # Load tamper data
        tamper = [POSSIBLE_COMPLETED, player[3], json.loads(player[1]).index(player[2]) + 1]

        # Render 'finish'
        resp = make_response(render_template("finish" + DEV + ".html", name=name,
                                             time=(player[5] - player[4]), tamperer=tamper))
        resp.set_cookie("data", "", expires=0)
        return resp

    # Check if already played
    if played:
        # Check if has highscore
        if STATISTICS["Highscore"][0] == name:
            # Notify new highscore
            Send.finisher(player, True)

            resp = make_response(render_template("finish" + DEV + ".html", name=name, time=(player[5] - player[4]),
                                                 played=played, hs=[prev[1], (prev[1] - (player[5]-player[4]))]))
            resp.set_cookie("data", "", expires=0)
            return resp

        # Notify new finisher
        Send.finisher(player)

        # Return basic played finish
        resp = make_response(render_template("finish" + DEV + ".html", name=name,
                                             time=(player[5] - player[4]), played=played))
        resp.set_cookie("data", "", expires=0)
        return resp

    # Check if user got highscore
    if STATISTICS["Highscore"][0] == name:
        # Notify new highscore
        Send.finisher(player, True)

        resp = make_response(render_template("finish" + DEV + ".html", name=name, time=(player[5] - player[4]),
                                             hs=[prev[1], (prev[1] - (player[5]-player[4]))]))
        resp.set_cookie("pstatus", "1", expires=(time() + 316000000))
        resp.set_cookie("data", "", expires=0)
        return resp

    # Notify new finisher
    Send.finisher(player)

    # Render finish
    resp = make_response(render_template("finish" + DEV + ".html", name=name, time=(player[5] - player[4])))
    resp.set_cookie("pstatus", "1", expires=(time() + 316000000))
    resp.set_cookie("data", "", expires=0)
    return resp


# Name: puzzle
# Purpose: listen for get requests, view a given puzzle
# Inputs:
# Outputs: rendered html
@app.route("/puzzle")
def puzzle():
    # Check user has started
    if not request.cookies.get("data"):
        return render_template("tamperer" + DEV + ".html")

    # Get cookie data
    cookie = get_data_from_cookie()

    # Validate data
    if not verify_data(cookie):
        # Update tamper statistics
        STATISTICS["Tamper Attempts"] += 1

        # Remove data cookie
        resp = make_response(render_template("tamperer" + DEV + ".html"))
        resp.set_cookie("data", "", expires=0)
        return resp

    # Select & return current puzzle's html
    player = UserData.query(cookie[0])
    data = Puzzles.data(player[2])
    return render_template("puzzle" + DEV + ".html", title=data[0], prompt=data[1],
                           number=json.loads(player[1]).index(player[2]) + 1)


# Name: check
# Purpose: listen for get & post requests, check answer for puzzle
# Inputs:
# Outputs: redirection
@app.route("/check", methods=["GET", "POST"])
def check():
    # Check if user has started
    if not request.cookies.get("data"):
        return render_template("tamperer" + DEV + ".html")

    # Redirect to puzzle if get request
    if request.method == "GET":
        return redirect(url_for("puzzle"))

    # Get cookie data
    cookie = get_data_from_cookie()
    # Validate data
    if not verify_data(cookie):
        # Update tamper statistics
        STATISTICS["Tamper Attempts"] += 1

        # Remove data cookie
        resp = make_response(render_template("tamperer" + DEV + ".html"))
        resp.set_cookie("data", "", expires=0)
        return resp

    # Get other data
    player = UserData.query(cookie[0])
    solution = Puzzles.solution(player[2])
    response = request.form.get("response")

    # Check if testing
    if TESTING and response == "override":
        # Update player's puzzle completions
        UserData.update(cookie[0], complete=player[3] + 1)
        player = UserData.query(cookie[0])

        # Check if finished
        if json.loads(player[1])[POSSIBLE_COMPLETED - 1] == player[2] and player[3] == POSSIBLE_COMPLETED:
            # Set end time & redirect to end page
            UserData.update(cookie[0], time_end=int(time()))
            return redirect(url_for("finish"))

        # Update player's current puzzle
        curr_puzzle = json.loads(player[1])[json.loads(player[1]).index(player[2]) + 1]
        UserData.update(cookie[0], current=curr_puzzle)

        # Redirect to new puzzle
        return redirect(url_for("puzzle"))

    # Validate response for strings, ints & booleans
    try:
        # Create true and false values
        true_values = ["True", "true", "T", "t"]
        false_values = ["False", "false", "F", "f"]
        # Check strings
        if type(solution) == str and response.lower() != solution:
            return redirect(url_for("puzzle"))
        # Check integers
        elif type(solution) == int and ("." in str(response) or int(response) != solution):
            return redirect(url_for("puzzle"))
        # Check floats
        elif type(solution) == float and float(response) != solution:
            return redirect(url_for("puzzle"))
        # Check booleans
        elif type(solution) == bool and solution is True and response not in true_values:
            return redirect(url_for("puzzle"))
        elif type(solution) == bool and solution is False and response not in false_values:
            return redirect(url_for("puzzle"))
    # Catch any errors
    except AttributeError:
        return redirect(url_for("puzzle"))
    except ValueError:
        return redirect(url_for("puzzle"))

    # Update puzzle completions
    Puzzles.update(player[2])

    # Update player's puzzle completions
    UserData.update(cookie[0], complete=player[3] + 1)
    player = UserData.query(cookie[0])

    # Check if value mismatch
    if (json.loads(player[1])[POSSIBLE_COMPLETED - 1] != player[2] and player[3] == POSSIBLE_COMPLETED) \
            or (json.loads(player[1])[POSSIBLE_COMPLETED - 1] == player[2] and player[3] != POSSIBLE_COMPLETED):
        # Update tampered value
        UserData.update(cookie[0], tampered=1)

        if player[3] >= POSSIBLE_COMPLETED:
            # Set end time & redirect to end page
            UserData.update(cookie[0], time_end=int(time()))
            return redirect(url_for("finish"))

    # Check if finished
    elif json.loads(player[1])[POSSIBLE_COMPLETED - 1] == player[2] and player[3] == POSSIBLE_COMPLETED:
        # Set end time & redirect to end page
        UserData.update(cookie[0], time_end=int(time()))
        return redirect(url_for("finish"))

    # Update player's current puzzle
    curr_puzzle = json.loads(player[1])[json.loads(player[1]).index(player[2]) + 1]
    UserData.update(cookie[0], current=curr_puzzle)

    # Redirect to next puzzle
    return redirect(url_for("puzzle"))


# Name: page
# Purpose: listen for get requests, handle 404 errors
# Inputs:
# Outputs: rendered html
@app.route("/<p>")
def page(p):
    return render_template("404" + DEV + ".html", page=p)


if __name__ == "__main__":
    # Start reporting loop
    report = Reporter()
    report.start()

    # Run main app
    app.run(host=ADDRESS, port=PORT, debug=DEBUG)

    # Stop reporting loop
    report.stop()
