from flask import Flask, request

app = Flask(__name__)

@app.route("/")
def start():
    return """<h1>Hello world.</h1> 
    <img src="https://www.ikw.uni-osnabrueck.de/fileadmin/_processed_/csm_IMG_8142_a755516634.jpg">
    <p>OK.</p>
    <a href='/about'>About</a>"""


@app.route("/about")
def about():
    return """<h1> ABOUT</h1>
    """