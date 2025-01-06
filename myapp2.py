from flask import Flask, request, render_template

app = Flask(__name__)
last_rev="none"

@app.route("/")
def start():
    return render_template('start.html')

@app.route("/reversed")
def reversed():
    rev = request.args['rev'][::-1]
    resp = render_template('reversed.html', rev=rev, last_rev=last_rev)
    last_rev = rev
    return resp

