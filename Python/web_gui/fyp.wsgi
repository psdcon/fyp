import sys
sys.path.insert(0, '/var/www/html/fyp')

from werkzeug.debug import DebuggedApplication
from fyp import app

application = DebuggedApplication(app, True)
