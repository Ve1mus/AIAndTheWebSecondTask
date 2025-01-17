import sys
import os
# Let's say your actual Flask code is in '/home/u072/public_html/AIAndTheWebSecondTask'
MY_PROJECT_PATH = "/home/u072/public_html/AIAndTheWebSecondTask"

sys.path.insert(0, MY_PROJECT_PATH)
os.chdir(MY_PROJECT_PATH)

from start import app
application = app
