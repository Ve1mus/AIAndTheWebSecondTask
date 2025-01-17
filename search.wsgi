import sys
import os
# Let's say your actual Flask code is in '/home/u065/public_html/myproject'
MY_PROJECT_PATH = "/home/u072/public_html/secondtask"

sys.path.insert(0, MY_PROJECT_PATH)
os.chdir(MY_PROJECT_PATH)

from start import app
application = app