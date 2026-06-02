import boto3
from botocore.exceptions import ClientError
import pymysql
import json
import time

from leaderboard_ops import (
    try_save_leaderboard,
    validate_player_name,
    validate_score_payload,
)
from rate_limit import check_rate_limit

CORS_HEADERS = {
    'Access-Control-Allow-Origin': 'https://wordhunter.io',
    'Content-Type': 'application/json',
}

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


def _json_response(status_code: int, payload):
    return {
        'statusCode': status_code,
        'headers': CORS_HEADERS,
        'body': json.dumps(payload),
    }


def _client_ip(event) -> str:
    headers = event.get("headers") or {}
    forwarded = headers.get("X-Forwarded-For") or headers.get("x-forwarded-for") or ""
    if forwarded:
        return str(forwarded).split(",")[0].strip()
    source = event.get("requestContext", {}).get("identity", {})
    return source.get("sourceIp") or "unknown"


def lambda_handler(event, context):
    http_method = event['httpMethod']
    puzzle = int(event['pathParameters']['puzzle'])
    body = None

    if not check_rate_limit(_client_ip(event)):
        return _json_response(
            429,
            {'message': 'Rate limit exceeded. Try again in one minute.'},
        )

    if http_method == 'POST':
        raw = event.get('body') or '{}'
        try:
            body = json.loads(raw) if isinstance(raw, str) else raw
        except json.JSONDecodeError:
            return _json_response(400, {'message': 'Invalid JSON body'})
        base_required = ('player', 'score', 'trophy')
        missing = [k for k in base_required if k not in body]
        if missing:
            return _json_response(
                400,
                {'message': f'Missing required field(s): {", ".join(missing)}'},
            )
        if 'scoreValidation' not in body:
            return _json_response(
                400,
                {'message': 'Missing required field: scoreValidation'},
            )

    conn = None
    try:
        conn = pymysql.connect(host=RDS_HOST, user=RDS_USER, passwd=RDS_PASSWORD, db=RDS_DB, connect_timeout=5)
    except Exception as e:
        return _json_response(500, {'message': f'Unable to connect to database: {str(e)}'})

    try:
        if http_method == 'GET':
            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT player, score, trophy FROM leaderboard WHERE puzzle={puzzle} ORDER BY score DESC, time LIMIT 10"
                )
                result = cur.fetchall()
            return _json_response(200, [list(row) for row in result])

        if http_method == 'POST':
            player = body['player']
            score = int(body['score'])
            trophy = body['trophy']
            time_stamp = int(time.time())

            with conn.cursor() as cur:
                name_error = validate_player_name(player)
                if name_error:
                    message = name_error
                else:
                    score_validation = body['scoreValidation']
                    if validate_score_payload(score_validation, score, trophy) != score:
                        message = (
                            f"Invalid score for player: {player} with:\n{score_validation}"
                        )
                    else:
                        message = try_save_leaderboard(
                            cur,
                            conn,
                            puzzle,
                            time_stamp,
                            player,
                            score,
                            trophy,
                            body.get("sessionId"),
                        )

                cur.execute(
                    f"SELECT player, score, trophy FROM leaderboard WHERE puzzle={puzzle} ORDER BY score DESC, time LIMIT 10"
                )
                result = cur.fetchall()
            return _json_response(
                200,
                {'message': message, 'top_10': [list(row) for row in result]},
            )

        return _json_response(405, {'message': f'Method not allowed: {http_method}'})
    finally:
        if conn is not None:
            conn.close()
