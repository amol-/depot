# -*- coding: utf-8 -*-
import os
import shutil
from nose import SkipTest
import uuid
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
                    uploaded_to=DepotManager.get_default(),
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

        uploaded_file = app.get(DepotManager.url_for('%(uploaded_to)s/%(last)s' % new_file))
        assert uploaded_file.body == FILE_CONTENT

    def test_headers_are_there(self):
        app = self.make_app()
        new_file = app.post('/create_file').json

        uploaded_file = app.get(DepotManager.url_for('%(uploaded_to)s/%(last)s' % new_file))
        assert uploaded_file.headers['Content-Type'] == 'text/plain'
        assert 'ETag' in uploaded_file.headers
        assert 'Last-Modified' in uploaded_file.headers
        assert 'Expires' in uploaded_file.headers

    def test_caching_unmodified(self):
        app = self.make_app()
        new_file = app.post('/create_file').json

        uploaded_file = app.get(DepotManager.url_for('%(uploaded_to)s/%(last)s' % new_file))
        last_modified = uploaded_file.headers['Last-Modified']

        unmodified_file = app.get('/depot/default/%(last)s' % new_file,
                                  headers=[('If-Modified-Since', last_modified)],
                                  status=304)
        assert 'Not Modified' in unmodified_file.status, unmodified_file

    def test_caching_etag(self):
        app = self.make_app()
        new_file = app.post('/create_file').json

        uploaded_file = app.get(DepotManager.url_for('%(uploaded_to)s/%(last)s' % new_file))
        etag = uploaded_file.headers['ETag']

        unmodified_file = app.get('/depot/default/%(last)s' % new_file,
                                  headers=[('If-None-Match', etag)],
                                  status=304)
        assert 'Not Modified' in unmodified_file.status, unmodified_file

    def test_post_is_forwarded_to_app(self):
        app = self.make_app()
        new_file = app.post('/create_file').json

        file_path = DepotManager.url_for('%(uploaded_to)s/%(last)s' % new_file)
        uploaded_file = app.post(file_path, status=404)
        assert 'Not Found' in uploaded_file.status, uploaded_file

    def test_forwards_to_app(self):
        app = self.make_app()
        new_file = app.post('/create_file').json

        files = app.get('/').json
        assert new_file['last'] in files['files'], (new_file, files)

    def test_404_on_missing_file(self):
        app = self.make_app()
        missing = app.get('/depot/default/hello', status=404)
        assert 'Not Found' in missing.status
        missing = app.get('/depot/nodepot', status=404)
        assert 'Not Found' in missing.status
        missing = app.get('/depot/nodepot/hello', status=404)
        assert 'Not Found' in missing.status

    def test_invalid_unmodified_header(self):
        app = self.make_app()
        new_file = app.post('/create_file').json

        uploaded_file = app.get(DepotManager.url_for('%(uploaded_to)s/%(last)s' % new_file))

        unmodified_file = app.get('/depot/default/%(last)s' % new_file,
                                  headers=[('If-Modified-Since', 'HELLO WORLD')],
                                  status=400)
        assert 'Bad Request' in unmodified_file.status, unmodified_file

    def test_public_url_gets_redirect(self):
        try:
            global S3Storage
            from depot.io.awss3 import S3Storage
        except ImportError:
            raise SkipTest('Boto not installed')

        env = os.environ
        access_key_id = env.get('AWS_ACCESS_KEY_ID')
        secret_access_key = env.get('AWS_SECRET_ACCESS_KEY')
        if access_key_id is None or secret_access_key is None:
            raise SkipTest('Amazon S3 credentials not available')

        PID = os.getpid()
        NODE = str(uuid.uuid1()).rsplit('-', 1)[-1]  # Travis runs multiple tests concurrently
        default_bucket_name = 'filedepot-%s' % (access_key_id.lower(), )
        cred = (access_key_id, secret_access_key)
        bucket_name = 'filedepot-testfs-%s-%s-%s' % (access_key_id.lower(), NODE, PID)

        DepotManager.configure('awss3', {'depot.backend': 'depot.io.awss3.S3Storage',
                                         'depot.access_key_id': access_key_id,
                                         'depot.secret_access_key': secret_access_key,
                                         'depot.bucket': bucket_name})
        DepotManager.set_default('awss3')

        app = self.make_app()
        new_file = app.post('/create_file').json

        file_path = DepotManager.url_for('%(uploaded_to)s/%(last)s' % new_file)
        uploaded_file = app.get(file_path)
        assert uploaded_file.body == FILE_CONTENT, uploaded_file
