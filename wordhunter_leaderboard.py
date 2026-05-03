from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent / ".env.local")
except ImportError:
    pass

from flask import Flask, request, jsonify
from flask_cors import CORS
from better_profanity import profanity
import pymysql
import time
import os

from config import score_trace_validation_enabled
from leaderboard_ops import get_next_letters, try_insert_leaderboard, validate_game

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

RDS_HOST = os.environ.get("RDS_HOST")
RDS_USER = os.environ.get("RDS_USER")
RDS_PASSWORD = os.environ.get("RDS_PASSWORD")
RDS_DB = os.environ.get("RDS_DB")

_CORS_HEADER = {"Access-Control-Allow-Origin": "https://wordhunter.io"}


@app.route("/leaderboard/<int:puzzle>", methods=["GET", "POST"])
def leaderboard(puzzle):
    validate_trace = score_trace_validation_enabled()

    if request.method == "GET":
        try:
            conn = pymysql.connect(
                host=RDS_HOST,
                user=RDS_USER,
                passwd=RDS_PASSWORD,
                db=RDS_DB,
                connect_timeout=5,
            )
        except Exception as e:
            return jsonify({"message": f"Unable to connect to database: {str(e)}"}), 500
        try:
            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT player, score, trophy FROM leaderboard WHERE puzzle={puzzle} ORDER BY score DESC, time LIMIT 10"
                )
                result = cur.fetchall()
        finally:
            conn.close()
        resp = jsonify([list(row) for row in result])
        for k, v in _CORS_HEADER.items():
            resp.headers[k] = v
        return resp

    body = request.get_json(silent=True)
    if body is None:
        return jsonify({"message": "Invalid JSON body"}), 400
    base_required = ("player", "score", "trophy")
    missing = [k for k in base_required if k not in body]
    if missing:
        return (
            jsonify(
                {"message": f'Missing required field(s): {", ".join(missing)}'}
            ),
            400,
        )
    if validate_trace and "scoreValidation" not in body:
        return (
            jsonify(
                {
                    "message": "Missing required field: scoreValidation (WORDHUNTER_VALIDATE_SCORE is enabled)",
                }
            ),
            400,
        )

    player = body["player"]
    score = int(body["score"])
    trophy = body["trophy"]
    time_stamp = int(time.time())

    try:
        conn = pymysql.connect(
            host=RDS_HOST,
            user=RDS_USER,
            passwd=RDS_PASSWORD,
            db=RDS_DB,
            connect_timeout=5,
        )
    except Exception as e:
        return jsonify({"message": f"Unable to connect to database: {str(e)}"}), 500

    try:
        with conn.cursor() as cur:
            if player == "" or profanity.contains_profanity(player):
                message = f"Invalid player name: {player}"
            elif validate_trace:
                score_validation = body["scoreValidation"]
                if score != validate_game(
                    score_validation, get_next_letters(puzzle), trophy
                ):
                    message = (
                        f"Invalid score for player: {player} with:\n{score_validation}"
                    )
                else:
                    message = try_insert_leaderboard(
                        cur, conn, puzzle, time_stamp, player, score, trophy
                    )
            else:
                message = try_insert_leaderboard(
                    cur, conn, puzzle, time_stamp, player, score, trophy
                )
            cur.execute(
                f"SELECT player, score, trophy FROM leaderboard WHERE puzzle={puzzle} ORDER BY score DESC, time LIMIT 10"
            )
            result = cur.fetchall()
    finally:
        conn.close()

    resp = jsonify({"message": message, "top_10": [list(row) for row in result]})
    for k, v in _CORS_HEADER.items():
        resp.headers[k] = v
    return resp


if __name__ == "__main__":
    app.run(debug=False)

# WSGI (e.g. PythonAnywhere) expects the name ``application``.
application = app
