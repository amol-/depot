# -*- coding: utf-8 -*-
import shutil

import tempfile, os, cgi, base64
from nose.tools import raises
from depot.manager import DepotManager

from tg import expose, TGController, AppConfig
from webtest import TestApp

FILE_CONTENT = b'HELLO WORLD'


class RootController(TGController):
    UPLOADED_FILES = []

    @expose('json')
    def index(self):
        return dict(files=self.UPLOADED_FILES)

    @expose('json')
    def clear_files(self):
        self.UPLOADED_FILES = []
        return dict(files=self.UPLOADED_FILES)

    @expose('json')
    def create_file(self):
        self.UPLOADED_FILES += [DepotManager.get().create(FILE_CONTENT,
                                                          filename='hello.txt')]
        return dict(files=self.UPLOADED_FILES,
                    last=self.UPLOADED_FILES[-1])


class TestWSGIMiddleware(object):
    @classmethod
    def setup_class(cls):
        config = AppConfig(minimal=True, root_controller=RootController())
        cls.wsgi_app = config.make_wsgi_app()

    def setup(self):
        DepotManager._clear()
        DepotManager.configure('default', {'depot.storage_path': './lfs'})

    def teardown(cls):
        shutil.rmtree('./lfs', ignore_errors=True)

    def make_app(self, **options):
        wsgi_app = DepotManager.make_middleware(self.wsgi_app, **options)
        return TestApp(wsgi_app)

    def test_serving_files(self):
        app = self.make_app()
        new_file = app.post('/create_file').json

        uploaded_file = app.get('/depot/default/%(last)s' % new_file)
        assert uploaded_file.body == FILE_CONTENT

    def test_headers_are_there(self):
        app = self.make_app()
        new_file = app.post('/create_file').json

        uploaded_file = app.get('/depot/default/%(last)s' % new_file)
        assert uploaded_file.headers['Content-Type'] == 'text/plain'
        assert 'ETag' in uploaded_file.headers
        assert 'Last-Modified' in uploaded_file.headers
        assert 'Expires' in uploaded_file.headers

    def test_caching_unmodified(self):
        app = self.make_app()
        new_file = app.post('/create_file').json

        uploaded_file = app.get('/depot/default/%(last)s' % new_file)
        last_modified = uploaded_file.headers['Last-Modified']

        unmodified_file = app.get('/depot/default/%(last)s' % new_file,
                                  headers=[('If-Modified-Since', last_modified)],
                                  status=304)
        assert 'Not Modified' in unmodified_file.status, unmodified_file

    def test_caching_etag(self):
        app = self.make_app()
        new_file = app.post('/create_file').json

        uploaded_file = app.get('/depot/default/%(last)s' % new_file)
        etag = uploaded_file.headers['ETag']

        unmodified_file = app.get('/depot/default/%(last)s' % new_file,
                                  headers=[('If-None-Match', etag)],
                                  status=304)
        assert 'Not Modified' in unmodified_file.status, unmodified_file

    def test_post_is_forwarded_to_app(self):
        app = self.make_app()
        new_file = app.post('/create_file').json

        file_path = ('/depot/default/%(last)s' % new_file).encode('ascii')
        uploaded_file = app.post(file_path, status=404)
        assert 'Not Found' in uploaded_file.status, uploaded_file
