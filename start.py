from flask import Flask, request, render_template

app = Flask(__name__)
last_rev="none"

@app.route("/")
def start():
    return render_template('start.html')

@app.route("/result")
def reversed():
    
    result = render_template('result.html')
    return result

