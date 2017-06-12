"""
WSGI config for depotexample project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/howto/deployment/wsgi/
"""

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "depotexample.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

# Configure a "default" storage based on DEPOT settings
from django.conf import settings
from depot.manager import DepotManager
DepotManager.configure('default', settings.DEPOT, prefix='')

# Wrap the application with depot middleware to serve files on /depot
application = DepotManager.make_middleware(application)