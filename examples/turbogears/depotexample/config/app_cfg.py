# -*- coding: utf-8 -*-
"""
Global configuration file for TG2-specific settings in depotexample.

This file complements development/deployment.ini.

"""

from tg.configuration import AppConfig

import depotexample
from depotexample import model
from depotexample.lib import app_globals, helpers 

base_config = AppConfig()
base_config.renderers = []

# True to prevent dispatcher from striping extensions
# For example /socket.io would be served by "socket_io" method instead of "socket"
base_config.disable_request_extensions = False

# Set None to disable escaping punctuation characters to "_" when dispatching methods.
# Set to a function to provide custom escaping.
base_config.dispatch_path_translator = True 
base_config.prefer_toscawidgets2 = True

base_config.package = depotexample

#Enable json in expose
base_config.renderers.append('json')
#Enable genshi in expose to have a lingua franca for extensions and pluggable apps
#you can remove this if you don't plan to use it.
base_config.renderers.append('genshi')

#Set the default renderer
base_config.default_renderer = 'genshi'
# if you want raw speed and have installed chameleon.genshi
# you should try to use this renderer instead.
# warning: for the moment chameleon does not handle i18n translations
#base_config.renderers.append('chameleon_genshi')
#Configure the base SQLALchemy Setup
base_config.use_sqlalchemy = True
base_config.model = depotexample.model
base_config.DBSession = depotexample.model.DBSession
# Configure the authentication backend

# YOU MUST CHANGE THIS VALUE IN PRODUCTION TO SECURE YOUR APP 
base_config.sa_auth.cookie_secret = "51899232-cef4-41f4-ae24-fef0362d6e1c"

base_config.auth_backend = 'sqlalchemy'

# what is the class you want to use to search for users in the database
base_config.sa_auth.user_class = model.User

from tg.configuration.auth import TGAuthMetadata

#This tells to TurboGears how to retrieve the data for your user
class ApplicationAuthMetadata(TGAuthMetadata):
    def __init__(self, sa_auth):
        self.sa_auth = sa_auth
    def authenticate(self, environ, identity):
        user = self.sa_auth.dbsession.query(self.sa_auth.user_class).filter_by(user_name=identity['login']).first()
        if user and user.validate_password(identity['password']):
            return identity['login']
    def get_user(self, identity, userid):
        return self.sa_auth.dbsession.query(self.sa_auth.user_class).filter_by(user_name=userid).first()
    def get_groups(self, identity, userid):
        return [g.group_name for g in identity['user'].groups]
    def get_permissions(self, identity, userid):
        return [p.permission_name for p in identity['user'].permissions]

base_config.sa_auth.dbsession = model.DBSession

base_config.sa_auth.authmetadata = ApplicationAuthMetadata(base_config.sa_auth)

# You can use a different repoze.who Authenticator if you want to
# change the way users can login
#base_config.sa_auth.authenticators = [('myauth', SomeAuthenticator()]

# You can add more repoze.who metadata providers to fetch
# user metadata.
# Remember to set base_config.sa_auth.authmetadata to None
# to disable authmetadata and use only your own metadata providers
#base_config.sa_auth.mdproviders = [('myprovider', SomeMDProvider()]

# override this if you would like to provide a different who plugin for
# managing login and logout of your application
base_config.sa_auth.form_plugin = None

# You may optionally define a page where you want users to be redirected to
# on login:
base_config.sa_auth.post_login_url = '/post_login'

# You may optionally define a page where you want users to be redirected to
# on logout:
base_config.sa_auth.post_logout_url = '/post_logout'
try:
    # Enable DebugBar if available, install tgext.debugbar to turn it on
    from tgext.debugbar import enable_debugbar
    enable_debugbar(base_config)
except ImportError:
    pass

from depot.manager import DepotManager
DepotManager.configure('default', {'depot.storage_path': '/tmp/'})
