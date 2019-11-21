from flask import Flask, abort, request

app = Flask(__name__)


@app.route('/o_auth2')
def o_auth2():
    if request.headers.get('Authorization') != 'Bearer token':
        abort(401)
    return ''


@app.route('/session_with_url_prefix', methods=('GET', 'POST', 'DELETE', 'PUT'))
def session_with_url_prefix():
    return ''


@app.route('/upload', methods=('POST',))
def upload():
    f = request.files['file']
    if f.filename != 'test.txt' or f.read() != b'upload':
        abort(400)
    return ''
