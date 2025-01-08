from flask import Flask, request, render_template

app = Flask(__name__)
last_rev="none"

@app.route("/")
def start():
    return render_template('start.html')

@app.route("/result")
def reversed():
    
    resp = render_template('result.html')
    return resp

