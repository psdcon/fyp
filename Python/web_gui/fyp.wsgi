import sys
sys.path.insert(0, '/var/www/html/fyp')

from fyp import app
from werkzeug.debug import DebuggedApplication
application = DebuggedApplication(app, True)
