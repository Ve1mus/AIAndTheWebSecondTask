import sys
import os

# Add the project directory to the sys.path
project_home = '/home/u072/public_html'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment variables
os.environ['FLASK_APP'] = 'start.py'
os.environ['FLASK_ENV'] = 'production'

# Activate the virtual environment
activate_this = '/home/u072/public_html/myenv/bin/activate'
with open(activate_this) as file_:
    exec(file_.read(), dict(__file__=activate_this))

# Import the Flask application
from start import app as application

