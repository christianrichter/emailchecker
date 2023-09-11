import os
from ipaddress import IPv4Address

import waitress
from flask import Flask
from flask import Response
from flask import jsonify
from flask import make_response
from validate_email import validate_email

app = Flask(__name__)


@app.route("/square/<int:base>", methods=["GET"])
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

    hostname = os.getenv('HOST_NAME')
    from_address = os.getenv('FROM_ADDRESS')

    print(f'running on {hostname} and using email sender address {from_address}')
    return make_response("", 200)


@app.route("/email/validate/<string:email>", methods=["GET"])
def verify_email(email):

    hostname = os.getenv('HOST_NAME')
    from_address = os.getenv('FROM_ADDRESS')

    print(f'checking {email}')

    is_valid = validate_email(
        email_address=email,
        check_format=True,
        check_blacklist=True,
        check_dns=True,
        dns_timeout=10,
        check_smtp=True,
        smtp_timeout=10,
        smtp_helo_host=hostname,
        smtp_from_address=from_address,
        smtp_skip_tls=False,
        smtp_tls_context=None,
        smtp_debug=True,
        address_types=frozenset([IPv4Address]))

    return jsonify(is_valid)


waitress.serve(app, host="0.0.0.0", port=int(os.getenv("SERVICE_PORT")))
