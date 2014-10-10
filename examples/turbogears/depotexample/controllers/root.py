# -*- coding: utf-8 -*-
"""Main Controller"""

from tg import expose, flash, require, url, lurl, request, redirect, tmpl_context
from tg.i18n import ugettext as _, lazy_ugettext as l_
from tg import predicates
from depotexample import model
from depotexample.controllers.secure import SecureController
from depotexample.model import DBSession, metadata
from tgext.admin.tgadminconfig import BootstrapTGAdminConfig as TGAdminConfig
from tgext.admin.controller import AdminController

from depotexample.lib.base import BaseController
from depotexample.controllers.error import ErrorController

__all__ = ['RootController']

from tgext.crud import EasyCrudRestController
from tgext.admin.config import CrudRestControllerConfig


class UploadedImageAdminController(EasyCrudRestController):
    """Custom TurboGears Admin to show images preview"""
    @classmethod
    def _preview_image(cls, filler, row):
        return '''
<a href="%(url)s">
    %(url)s
</a>
<div style="width:320px;height:240px;background: url('%(url)s') center / contain no-repeat"></div>
''' % dict(url=row.file.url)

    __table_options__ = {'__xml_fields__': ['file'],
                         'file': lambda *args: UploadedImageAdminController._preview_image(*args)}


class CustomAdminConfig(TGAdminConfig):
    class uploadedimage(CrudRestControllerConfig):
        defaultCrudRestController = UploadedImageAdminController


class RootController(BaseController):
    """
    The root controller for the depotexample application.

    All the other controllers and WSGI applications should be mounted on this
    controller. For example::

        panel = ControlPanelController()
        another_app = AnotherWSGIApplication()

    Keep in mind that WSGI applications shouldn't be mounted directly: They
    must be wrapped around with :class:`tg.controllers.WSGIAppController`.

    """
    secc = SecureController()
    admin = AdminController(model, DBSession, config_type=CustomAdminConfig)

    error = ErrorController()

    def _before(self, *args, **kw):
        tmpl_context.project_name = "depotexample"

    @expose('depotexample.templates.index')
    def index(self):
        """Handle the front-page."""
        return dict(page='index')

    @expose('depotexample.templates.about')
    def about(self):
        """Handle the 'about' page."""
        return dict(page='about')

    @expose('depotexample.templates.environ')
    def environ(self):
        """This method showcases TG's access to the wsgi environment."""
        return dict(page='environ', environment=request.environ)

    @expose('depotexample.templates.data')
    @expose('json')
    def data(self, **kw):
        """This method showcases how you can use the same controller for a data page and a display page"""
        return dict(page='data', params=kw)
    @expose('depotexample.templates.index')
    @require(predicates.has_permission('manage', msg=l_('Only for managers')))
    def manage_permission_only(self, **kw):
        """Illustrate how a page for managers only works."""
        return dict(page='managers stuff')

    @expose('depotexample.templates.index')
    @require(predicates.is_user('editor', msg=l_('Only for the editor')))
    def editor_user_only(self, **kw):
        """Illustrate how a page exclusive for the editor works."""
        return dict(page='editor stuff')

    @expose('depotexample.templates.login')
    def login(self, came_from=lurl('/')):
        """Start the user login."""
        login_counter = request.environ.get('repoze.who.logins', 0)
        if login_counter > 0:
            flash(_('Wrong credentials'), 'warning')
        return dict(page='login', login_counter=str(login_counter),
                    came_from=came_from)

    @expose()
    def post_login(self, came_from=lurl('/')):
        """
        Redirect the user to the initially requested page on successful
        authentication or redirect her back to the login page if login failed.

        """
        if not request.identity:
            login_counter = request.environ.get('repoze.who.logins', 0) + 1
            redirect('/login',
                params=dict(came_from=came_from, __logins=login_counter))
        userid = request.identity['repoze.who.userid']
        flash(_('Welcome back, %s!') % userid)
        redirect(came_from)

    @expose()
    def post_logout(self, came_from=lurl('/')):
        """
        Redirect the user to the initially requested page on logout and say
        goodbye as well.

        """
        flash(_('We hope to see you soon!'))
        redirect(came_from)
