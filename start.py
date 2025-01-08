from flask import Flask, request, render_template

app = Flask(__name__)
last_rev="none"

@app.route("/")
def start():
    return render_template('start.html')

@app.route("/result")
def result():
    
    result = render_template('result.html')
    return result


@app.route("/error")
def error():
    
    error = render_template('error.html')
    return error
