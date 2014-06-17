# -*- coding: utf-8 -*-

import tempfile, os, shutil, cgi, base64
from PIL import Image
from sqlalchemy.schema import Column
from sqlalchemy.types import Unicode, Integer
from .base_sqla import setup_database, clear_database, DeclarativeBase, DBSession
from depot.fields.sqlalchemy import UploadedFileField
from depot.manager import DepotManager, get_file
from .utils import create_cgifs
from depot.fields.specialized.image import UploadedImageWithThumb


def setup():
    setup_database()

    DepotManager._clear()
    DepotManager.configure('default', {'depot.storage_path': './lfs'})
    DepotManager.make_middleware(None)


def teardown():
    #shutil.rmtree('./lfs', ignore_errors=True)
    pass


class Document(DeclarativeBase):
    __tablename__ = 'docu'

    uid = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(Unicode(16), unique=True)
    content = Column('content_col', UploadedFileField)
    photo = Column(UploadedFileField(upload_type=UploadedImageWithThumb))


class TestSQLAAttachments(object):
    def __init__(self):
        self.file_content = 'this is the file content'
        self.fake_file = tempfile.NamedTemporaryFile()
        self.fake_file.write(self.file_content)
        self.fake_file.flush()

    def setup(self):
        clear_database()

    def test_create_fromfile(self):
        doc = Document(name=u'Foo')
        doc.content = open(self.fake_file.name)
        DBSession.add(doc)
        DBSession.flush()
        DBSession.commit()

        d = DBSession.query(Document).filter_by(name=u'Foo').first()
        assert d.content.file.read() == self.file_content
        assert d.content.file.filename == os.path.basename(self.fake_file.name)

    def test_edit_existing(self):
        doc = Document(name=u'Foo2')
        doc.content = open(self.fake_file.name)
        DBSession.add(doc)
        DBSession.flush()
        DBSession.commit()
        DBSession.remove()

        d = DBSession.query(Document).filter_by(name=u'Foo2').first()
        old_file =  d.content.path

        d.content = 'HELLO'
        new_file = d.content.path

        DBSession.flush()
        DBSession.commit()
        DBSession.remove()

        f = get_file(new_file).read() == 'HELLO'

        try:
            fold = get_file(old_file)
            assert False, 'Should have raised IOError here'
        except IOError:
            pass

    def test_edit_existing_rollback(self):
        doc = Document(name=u'Foo3')
        doc.content = open(self.fake_file.name)
        DBSession.add(doc)
        DBSession.flush()
        DBSession.commit()
        DBSession.remove()

        d = DBSession.query(Document).filter_by(name=u'Foo3').first()
        old_file =  d.content.path

        d.content = 'HELLO'
        new_file = d.content.path

        DBSession.flush()
        DBSession.rollback()
        DBSession.remove()

        f = get_file(old_file).read() == self.file_content

        try:
            fold = get_file(new_file)
            assert False, 'Should have raised IOError here'
        except IOError:
            pass

    def test_create_fromfield(self):
        field = create_cgifs('image/jpeg', self.fake_file, 'test.jpg')

        doc = Document(name=u'Foo', content=field)
        DBSession.add(doc)
        DBSession.flush()
        DBSession.commit()

        d = DBSession.query(Document).filter_by(name=u'Foo').first()
        assert d.content.file.read() == self.file_content
        assert d.content.filename == 'test.jpg'
        assert d.content.content_type == 'image/jpeg', d.content.content_type
        assert d.content.url == '/depot/%s' % d.content.path

    def test_create_empty(self):
        doc = Document(name=u'Foo', content=None)
        DBSession.add(doc)
        DBSession.flush()
        DBSession.commit()

        d = DBSession.query(Document).filter_by(name=u'Foo').first()
        assert d.content is None


class TestSQLAImageAttachments(object):
    def __init__(self):
        self.file_content = '''R0lGODlhEQAUAPcAAC4uLjAwMDIyMjMzMjQ0NDU1NDY2Njk2Mzg4ODo6Oj49Ozw8PD4+PkE+OEA/PkhAN0tCNk5JPFFGNV1KMFhNNVFHOFJJPVVLPVhOPXZfKXVcK2ZQNGZXNGtZMnNcNHZeNnldMHJfOn1hKXVjOH9oO0BAQEJCQkREREVFREZGRklGQ05KQ0hISEpKSkxMTE5OTlZRSlFQT19XSFBQUFJSUlRUVGFUQmFVQ2ZZQGtdQnNiQqJ/HI1uIYBnLIllKoZrK4FqLoVqL4luLIpsLpt7J515JJ50KZhzLYFnMIFlM4ZlMIFkNI1uNoJoOoVrPIlvO49yMolwPpB2O5p4Op98PaB3IKN4JqN8J6h7I6J5LaZ+LLF+ILGGG7+JG72OGLKEI7aHIrOEJL2JI7mMN76YNcGJG8SOG8WLHMONH86eEs+aFsGSG8eQHMySG9uVFduXFdeeE9eaFdScF96YE9yaFOKcEuOdEtWgFNiiEduhE96pEuqlD+qmD+KpD+yoDu6rDuysDvCuDfCvDeuwD/SzC/a2CvGwDfKxDPi5Cfi5Cvq8CeCjEuehEOagEeijEOKoEOStFMOOK8+TLM6YNNChItGgLtylKt6gMNqgON6jPOChLfi/JOSrNeGvN9KhRtykRNWkSOCnQOCpSOawQue1T+a6Su67SOGsUO/AVAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACH5BAAAAAAALAAAAAARABQAAAj+AAEIHEiwoMAACBMqXIhQgMOHDwdAfEigYsUCT6KQScNjxwGLBAyINPBhCilUmxIV6uMlw0gEMJeMGWWqFCU8hA4JEgETQYIEDcRw6qRlwgMIGvJwkfAzwYIFXQBB8qHg6VMKFawuYNBBjaIqDhhI+cGgrNmyJXooGrShBJBKcIpwiFCibl0TehDdsWBCiBxLZuIwolMGiwcTJ4gUenThBAokSVRgGFJnzhYQJ1KsyRkkhWfPK87McWPEM4sRhgItCsGitQ5PmtxYUdK6BY4rf/zwYRNmUihRpyQdaUHchQsoX/Y4amTnUqZPoG7YMO7ihfUcYNC0eRMJExMqMKweW59BfkYMEk2ykHAio3x5GvDjy58Pv4b9+/jz2w8IADs='''
        self.file_content = base64.b64decode(self.file_content)
        self.fake_file = tempfile.NamedTemporaryFile()
        self.fake_file.write(self.file_content)
        self.fake_file.flush()

    def setup(self):
        clear_database()
        self.fake_file.seek(0)

    def test_create_fromfile(self):
        doc = Document(name=u'Foo')
        doc.photo = open(self.fake_file.name)
        DBSession.add(doc)
        DBSession.flush()
        DBSession.commit()

        d = DBSession.query(Document).filter_by(name=u'Foo').first()
        assert d.photo.file.read() == self.file_content
        assert d.photo.filename == os.path.basename(self.fake_file.name)

    def test_create_fromfield(self):
        field = cgi.FieldStorage()
        field.filename = u'àèìòù.gif'
        field.file = open(self.fake_file.name)

        doc = Document(name=u'Foo', photo=field)
        DBSession.add(doc)
        DBSession.flush()
        DBSession.commit()

        d = DBSession.query(Document).filter_by(name=u'Foo').first()
        assert d.photo.file.read() == self.file_content
        assert d.photo.filename == field.filename
        assert d.photo.url == '/depot/%s' % d.photo.path
        assert d.photo.thumb_url == '/depot/%s' % d.photo.thumb_path
        assert d.photo.url != d.photo.thumb_url

    def test_thumbnail(self):
        field = create_cgifs('image/gif', self.fake_file, 'test.gif')

        doc = Document(name=u'Foo', photo=field)
        DBSession.add(doc)
        DBSession.flush()
        DBSession.commit()

        d = DBSession.query(Document).filter_by(name=u'Foo').first()
        assert os.path.exists(d.photo.thumb_file._file_path)

        thumb = Image.open(d.photo.thumb_file._file_path)
        thumb.verify()
        assert thumb.format.upper() == d.photo.thumbnail_format.upper()

    def test_public_url(self):
        doc = Document(name=u'Foo')
        doc.photo = open(self.fake_file.name)
        doc.content = open(self.fake_file.name)
        DBSession.add(doc)
        DBSession.flush()
        DBSession.commit()

        d = DBSession.query(Document).filter_by(name=u'Foo').first()
        d.photo['_public_url'] = 'PUBLIC_URL'
        d.photo['_thumb_public_url'] = 'THUMB_PUBLIC_URL'
        assert d.photo.url == 'PUBLIC_URL'
        assert d.photo.thumb_url == 'THUMB_PUBLIC_URL'

    def test_rollback(self):
        doc = Document(name=u'Foo3')
        doc.photo = open(self.fake_file.name)
        DBSession.add(doc)
        DBSession.flush()

        uploaded_file = doc.photo.path
        uploaded_thumb = doc.photo.thumb_path

        DBSession.rollback()
        DBSession.remove()

        try:
            fold = get_file(uploaded_file)
            assert False, 'Should have raised IOError here'
        except IOError:
            pass

        try:
            fold = get_file(uploaded_thumb)
            assert False, 'Should have raised IOError here'
        except IOError:
            pass
