# Krantz-Challenge
###### Version: 0.1.122617


## Overview

Krantz's Challenge is a game consiting solely of a set of currently 16 puzzles that are randomly given to each player. Currently, 4 random puzzles are given to the player and to "win," they must finish all of them. The number of puzzles and puzzles to complete is subject to change. There is no authentication needed, as the player's id is stored in a persistent browser cookie. It is fully extensible to add whatever features you would like. See below for adding new features.


## Run Your Own

### Installation
Follow the below steps to install the server:
```
git clone git@bitbucket.org:akrantz/krantz-challenge.git
cd krantz-challenge

(Linux/MacOS) pip3 install -r requirements.txt
(Windows) python -m pip install -r requirements.txt
```

### Start the Server
Before you run `server.py`, edit the following variables to match your desired configuration:

| Variable            | Default Value   | Format  | Description                                            |
| ------------------- | --------------- | ------- | ------------------------------------------------------ |
| TO                  | "test@test.com" | String  | Email for sending statistics to                        |
| FROM                | "test@test.com" | String  | Mailgun email for sending statistics from              |
| MG_APIKEY           | "key"           | String  | Mailgun API key                                        |
| GH_API              | "username:key"  | String  | Github username and personal access token              |
| GH_ID               | "id"            | String  | Github Gist id                                         |
| POSSIBLE\_COMPLETED | 4               | Integer | Number of puzzles a player is required to complete     |
| ADDRESS             | "127.0.0.1"     | String  | Address for Flask to listen on                         |
| PORT                | 5000            | Integer | Port for Flask to run on                               |
| DEBUG               | True            | Boolean | Run flask in debug mode or not                         |
| TESTING             | False           | Boolean | Add override for answers in testing                    |
| DEV                 | ""              | String  | prefix of the final name before the .html              |
| DOMAIN              | "test.com"      | String  | Mailgun registered domain to send from                 |
| DATABASE_HOST       | "127.0.0.1"     | String  | IP address where the MySQL database is hosted          |
| DATABASE_PORT       | "3306"          | String  | Port on server where MySQL server is running           |
| DATABASE_USER       | "username"      | String  | Username for the MySQL user                            |
| DATABASE_PASS       | "password"      | String  | Password for the MySQL user                            |
| DATABASE_DATABASE   | "game"          | String  | Database to store everything on the MySQL server       |
| DATABASE_OPTIONS    | ""              | String  | Database connection options (ex. SSL)                  |

Type the following into the terminal (Linux/MacOS) or command prompt (Windows): `python3 server.py`


## Development

### Contribution instructions
Follow the below steps to contribute:
1. Submit a pull request w/ a description of modifications
2. Wait for it to be reviewed by myself or another owner
3. Make any changes necessary

### Other guidelines
* Try not to include other modules
* Follow the [PEP 8](https://www.python.org/dev/peps/pep-0008) style guide as closely as possible
	* Note: typing is not required
* Check issues first before submitting your own


## Contact
Contact me at [krantzie124@gmail.com](mailto:krantzie124@gmail.com). I will try to get back to you within 24 hours.