import boto3
from botocore.exceptions import ClientError
from better_profanity import profanity
from collections import deque
import pymysql
import json
import time

def get_secret():

    secret_name = "test/wordhunterLeaderboard"
    region_name = "us-west-2"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        raise e

    secret = get_secret_value_response['SecretString']

    return json.loads(secret)

secret = get_secret()
RDS_HOST = secret["RDS_HOST"]
RDS_USER = secret["RDS_USER"]
RDS_PASSWORD = secret["RDS_PASSWORD"]
RDS_DB = secret["RDS_DB"]


def word_score(word):
    if len(word) <= 3:
        return len(word)
    else:
        return 3 + sum(range(2, len(word) - 1))

def validate_turn(word, letters, replacement_count, next_letters):
    # Check if each letter in the word exists in the letters
    for letter in set(word):
        if letter not in letters:
            return False, None

    # Build validation board for the next turn
    validation_board = list(letters)
    for letter in set(word):
        if letter in validation_board:
            validation_board.remove(letter)

    # Replace letters with next letters
    for _ in range(replacement_count):
        if next_letters:
            validation_board.append(next_letters.popleft())
        else:
            validation_board.append(" ")

    return True, "".join(validation_board)


def validate_game(validation_data, next_letters):
    if not validation_data:
        return 0
    score = 0
    next_letters = deque(next_letters)
    for idx, turn_data in enumerate(validation_data):
        word, letters, replacement_count = turn_data
        if replacement_count < 3:
            return 0
        score += word_score(word)
        is_valid, validation_board = validate_turn(
            word, letters, replacement_count, next_letters
        )
        if not is_valid:
            return 0

        # Check if next turn letters are contained in current validation board
        if idx + 1 < len(validation_data):
            next_turn_letters = set(validation_data[idx + 1][1])
            if not all(letter in validation_board for letter in next_turn_letters):
                return 0

    return score

def get_next_letters(puzzleNumber):
    with open('nextletters.txt', 'r') as file:
        lines = file.readlines()
        if puzzleNumber < len(lines):
            next_letters = lines[puzzleNumber].strip()
        else:
            next_letters = None
    return next_letters

def get_next_letters(puzzle):
    with open('nextletters.txt', 'r') as file:
        lines = file.readlines()
        if puzzle < len(lines):
            next_letters = lines[puzzle].strip()
        else:
            next_letters = None

    return next_letters


def lambda_handler(event, context):
    http_method = event['httpMethod']
    puzzle = int(event['pathParameters']['puzzle'])
    
    try:
        conn = pymysql.connect(host=RDS_HOST, user=RDS_USER, passwd=RDS_PASSWORD, db=RDS_DB, connect_timeout=5)
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'message': f'Unable to connect to database: {str(e)}'})
        }

    if http_method == 'GET':
        with conn.cursor() as cur:
            cur.execute(f"SELECT player, score, trophy FROM leaderboard WHERE puzzle={puzzle} ORDER BY score DESC, time LIMIT 10")
            result = cur.fetchall()
        conn.close()
        return {
            'statusCode': 200,
            'headers':{'Access-Control-Allow-Origin': 'https://wordhunter.onrender.com'},
            'body': json.dumps(result)
        }
    elif http_method == 'POST':
        body = json.loads(event['body']) 
        player = body['player']
        score = int(body['score'])
        trophy = body['trophy']
        score_validation = body['scoreValidation']
        time_stamp = int(time.time())

        with conn.cursor() as cur:
            if player == "" or profanity.contains_profanity(player):
                message = f"Invalid player name: {player}"
            elif score != validate_game(score_validation, get_next_letters(puzzle)):
                message = f"Invalid score for player: {player} with:\n{score_validation}"
            else:
                cur.execute(f"SELECT COUNT(*) FROM leaderboard WHERE puzzle={puzzle} AND player='{player}' AND score={score} AND trophy='{trophy}'")
                if cur.fetchone()[0] == 0:
                    cur.execute(f"INSERT INTO leaderboard (puzzle, time, player, score, trophy) VALUES ({puzzle}, {time_stamp}, '{player}', {score}, '{trophy}')")
                    conn.commit()
                    message = 'Record inserted successfully.'
                else:
                    message = 'This record already exists.'
            cur.execute(f"SELECT player, score, trophy FROM leaderboard WHERE puzzle={puzzle} ORDER BY score DESC, time LIMIT 10")
            result = cur.fetchall()
        conn.close()
        return {
            'statusCode': 200,
            'headers':{'Access-Control-Allow-Origin': 'https://wordhunter.onrender.com'},
            'body': json.dumps({
                'message': message,
                'top_10': result
            })
        }
