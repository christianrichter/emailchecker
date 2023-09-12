import os
from dataclasses import dataclass
from http.client import HTTPConnection
from ipaddress import IPv4Address

import flask_praetorian
import waitress
from flask import Flask
from flask import Response
from flask import jsonify
from flask import make_response
from flask import request
from validate_email import validate_email


guard = flask_praetorian.Praetorian()

API_PASS = os.getenv('API_PASS')
HOSTNAME = os.getenv('HOST_NAME')
FROM_ADDRESS = os.getenv('FROM_ADDRESS')


@dataclass
class User:

    id: int
    hashed_password: str

    @property
    def identity(self):
        return self.id

    @property
    def rolenames(self):
        return []

    @property
    def password(self):
        return self.hashed_password

    @classmethod
    def lookup(cls, username):
        user = None
        if username == 'api-user':
            user = User(id=12, hashed_password=guard.hash_password(API_PASS))
        return user

    @classmethod
    def identify(cls, id):
        user = None
        if id == 12:
            user = User(id=12, hashed_password=API_PASS)
        return user


app = Flask(__name__)



with app.app_context():
    app.debug = True
    app.config['SECRET_KEY'] = 'top_secret'
    app.config['JWT_ACCESS_LIFESPAN'] = {'hours': 24}
    app.config['JWT_REFRESH_LIFESPAN'] = {'days': 30}
    guard.init_app(app, User)


@app.route('/login', methods=['POST'])
def login():
    print(request)
    req = request.get_json(force=True)
    print(req)
    password = req.get('password', None)
    username = 'api-user'
    user = guard.authenticate(username, password)
    response = {'access_token': guard.encode_jwt_token(user)}
    return (jsonify(response), 200)


@app.route("/square/<int:base>", methods=["GET"])
@flask_praetorian.auth_required
def square(base): # pylint: disable=unused-variable
    square_product = base * base

    resp = Response(str(square_product), status=200)
    resp.headers["Access-Control-Allow-Origin"] = "*" # enables CORS for JS Fetch requests

    return resp


@app.route("/health", methods=["GET"])
def health():
    return make_response("", 200)


@app.route("/info", methods=["GET"])
def info():

    print(f'running on {HOSTNAME} and using email sender address {FROM_ADDRESS}')
    return make_response("", 200)


@app.route("/email/validate/<string:email>", methods=["GET"])
@flask_praetorian.auth_required
def verify_email(email):

    print(f'checking {email}')

    is_valid = validate_email(
        email_address=email,
        check_format=True,
        check_blacklist=True,
        check_dns=True,
        dns_timeout=10,
        check_smtp=True,
        smtp_timeout=10,
        smtp_helo_host=HOSTNAME,
        smtp_from_address=FROM_ADDRESS,
        smtp_skip_tls=False,
        smtp_tls_context=None,
        smtp_debug=True,
        address_types=frozenset([IPv4Address]))

    return jsonify(is_valid)


# Run the example
# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5000)


waitress.serve(app, host="0.0.0.0", port=int(os.getenv("SERVICE_PORT")))
