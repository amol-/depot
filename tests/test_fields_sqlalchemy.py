# -*- coding: utf-8 -*-

import tempfile, os, shutil, cgi, base64
from PIL import Image
from sqlalchemy.schema import Column
from sqlalchemy.types import Unicode, Integer
from .base_sqla import setup_database, clear_database, DeclarativeBase, DBSession, Thing
from depot.fields.sqlalchemy import FileField


def setup():
    setup_database()

def teardown():
    shutil.rmtree('./lfs', ignore_errors=True)


class Document(DeclarativeBase):
    __tablename__ = 'docu'

    uid = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(Unicode(16), unique=True)
    content = Column(FileField)
    photo = Column(FileField(AttachedImage))

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
        assert d.content.filename == os.path.basename(self.fake_file.name)

    def test_create_fromfield(self):
        field = cgi.FieldStorage()
        field.filename = 'test.jpg'
        field.file = open(self.fake_file.name)

        doc = Document(name=u'Foo', content=field)
        DBSession.add(doc)
        DBSession.flush()
        DBSession.commit()

        d = DBSession.query(Document).filter_by(name=u'Foo').first()
        assert d.content.file.read() == self.file_content
        assert d.content.filename == os.path.basename('test.jpg')
        assert d.content.url.startswith('/attachments')
        assert d.content.url.endswith('test.jpg')

class TestSQLAImageAttachments(object):
    def __init__(self):
        self.file_content = '''R0lGODlhEQAUAPcAAC4uLjAwMDIyMjMzMjQ0NDU1NDY2Njk2Mzg4ODo6Oj49Ozw8PD4+PkE+OEA/PkhAN0tCNk5JPFFGNV1KMFhNNVFHOFJJPVVLPVhOPXZfKXVcK2ZQNGZXNGtZMnNcNHZeNnldMHJfOn1hKXVjOH9oO0BAQEJCQkREREVFREZGRklGQ05KQ0hISEpKSkxMTE5OTlZRSlFQT19XSFBQUFJSUlRUVGFUQmFVQ2ZZQGtdQnNiQqJ/HI1uIYBnLIllKoZrK4FqLoVqL4luLIpsLpt7J515JJ50KZhzLYFnMIFlM4ZlMIFkNI1uNoJoOoVrPIlvO49yMolwPpB2O5p4Op98PaB3IKN4JqN8J6h7I6J5LaZ+LLF+ILGGG7+JG72OGLKEI7aHIrOEJL2JI7mMN76YNcGJG8SOG8WLHMONH86eEs+aFsGSG8eQHMySG9uVFduXFdeeE9eaFdScF96YE9yaFOKcEuOdEtWgFNiiEduhE96pEuqlD+qmD+KpD+yoDu6rDuysDvCuDfCvDeuwD/SzC/a2CvGwDfKxDPi5Cfi5Cvq8CeCjEuehEOagEeijEOKoEOStFMOOK8+TLM6YNNChItGgLtylKt6gMNqgON6jPOChLfi/JOSrNeGvN9KhRtykRNWkSOCnQOCpSOawQue1T+a6Su67SOGsUO/AVAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACH5BAAAAAAALAAAAAARABQAAAj+AAEIHEiwoMAACBMqXIhQgMOHDwdAfEigYsUCT6KQScNjxwGLBAyINPBhCilUmxIV6uMlw0gEMJeMGWWqFCU8hA4JEgETQYIEDcRw6qRlwgMIGvJwkfAzwYIFXQBB8qHg6VMKFawuYNBBjaIqDhhI+cGgrNmyJXooGrShBJBKcIpwiFCibl0TehDdsWBCiBxLZuIwolMGiwcTJ4gUenThBAokSVRgGFJnzhYQJ1KsyRkkhWfPK87McWPEM4sRhgItCsGitQ5PmtxYUdK6BY4rf/zwYRNmUihRpyQdaUHchQsoX/Y4amTnUqZPoG7YMO7ihfUcYNC0eRMJExMqMKweW59BfkYMEk2ykHAio3x5GvDjy58Pv4b9+/jz2w8IADs='''
        self.file_content = base64.b64decode(self.file_content)
        self.fake_file = tempfile.NamedTemporaryFile()
        self.fake_file.write(self.file_content)
        self.fake_file.flush()

    def setup(self):
        clear_database()

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
        assert d.photo.url.startswith('/attachments/')
        assert d.photo.url.endswith(field.filename)

    def test_thumbnail(self):
        field = cgi.FieldStorage()
        field.filename = 'test.gif'
        field.file = open(self.fake_file.name)

        doc = Document(name=u'Foo', photo=field)
        DBSession.add(doc)
        DBSession.flush()
        DBSession.commit()

        d = DBSession.query(Document).filter_by(name=u'Foo').first()
        assert os.path.exists(d.photo.thumb_local_path)

        thumb = Image.open(d.photo.thumb_local_path)
        thumb.verify()
        assert thumb.format.upper() == d.photo.thumbnail_format.upper()