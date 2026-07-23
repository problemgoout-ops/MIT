import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

import pymysql
pymysql.install_as_MySQLdb()

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
