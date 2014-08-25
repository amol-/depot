# -*- coding: utf-8 -*-
import shutil

import tempfile, os, cgi, base64
from PIL import Image
from depot.fields.filters.thumbnails import WithThumbnailFilter
from depot.fields.ming import UploadedFileProperty
from depot.manager import DepotManager, get_file
from .base_ming import setup_database, clear_database, DBSession
from ming.odm.declarative import MappedClass
from ming.odm import FieldProperty
from ming import schema as s, Field
from .utils import create_cgifs
from depot.fields.specialized.image import UploadedImageWithThumb
from depot._compat import u_
from nose import SkipTest


def setup():
    setup_database()

    DepotManager._clear()
    DepotManager.configure('default', {'depot.storage_path': './lfs'})
    DepotManager.make_middleware(None)


def teardown():
    shutil.rmtree('./lfs', ignore_errors=True)


class Document(MappedClass):
    class __mongometa__:
        session = DBSession
        name = 'depot_test_document'

    _id = FieldProperty(s.ObjectId)
    name = FieldProperty(str)
    content = UploadedFileProperty()
    photo = UploadedFileProperty(upload_type=UploadedImageWithThumb)
    second_photo = UploadedFileProperty(filters=(WithThumbnailFilter((12, 12), 'PNG'),))


class TestMingAttachments(object):
    def __init__(self):
        self.file_content = b'this is the file content'
        self.fake_file = tempfile.NamedTemporaryFile()
        self.fake_file.write(self.file_content)
        self.fake_file.flush()

    def setup(self):
        clear_database()

    def test_create_fromfile(self):
        doc = Document(name='Foo', content = open(self.fake_file.name, 'rb'))
        DBSession.flush()
        DBSession.clear()

        d = Document.query.find(dict(name='Foo')).first()
        assert d.content.file.read() == self.file_content
        assert d.content.file.filename == os.path.basename(self.fake_file.name)

    def test_create_fromfile_flush_single_document(self):
        doc = Document(name='Foo', content = open(self.fake_file.name, 'rb'))
        DBSession.flush(doc)
        DBSession.clear()

        d = Document.query.find(dict(name='Foo')).first()
        assert d.content.file.read() == self.file_content
        assert d.content.file.filename == os.path.basename(self.fake_file.name)

    def test_edit_existing(self):
        doc = Document(name=u_('Foo2'))
        doc.content = open(self.fake_file.name, 'rb')
        DBSession.flush()
        DBSession.clear()

        d = Document.query.find(dict(name='Foo2')).first()
        old_file = d.content.path

        d.content = b'HELLO'
        new_file = d.content.path

        DBSession.flush()
        DBSession.clear()


        assert get_file(new_file).read() == b'HELLO'

        try:
            fold = get_file(old_file)
            assert False, 'Should have raised IOError here'
        except IOError:
            pass

    def test_edit_existing_rollback(self):
        doc = Document(name=u_('Foo3'))
        doc.content = open(self.fake_file.name, 'rb')
        DBSession.flush()
        DBSession.clear()


        d = Document.query.find(dict(name='Foo3')).first()
        old_file = d.content.path

        d.content = b'HELLO'
        new_file = d.content.path

        DBSession.clear()
        assert get_file(old_file).read() == self.file_content

        raise SkipTest("Currently Ming Doesn't provide a way to handle discarded documents")
        try:
            fold = get_file(new_file)
            assert False, 'Should have raised IOError here'
        except IOError:
            pass

    def test_create_fromfield(self):
        field = create_cgifs('image/jpeg', self.fake_file, 'test.jpg')

        doc = Document(name=u_('Foo'), content=field)
        DBSession.flush()
        DBSession.clear()

        d = Document.query.find(dict(name='Foo')).first()
        assert d.content.file.read() == self.file_content
        assert d.content.filename == 'test.jpg'
        assert d.content.content_type == 'image/jpeg', d.content.content_type
        assert d.content.url == '/depot/%s' % d.content.path

    def test_create_empty(self):
        doc = Document(name=u_('Foo'), content=None)
        DBSession.flush()
        DBSession.clear()

        d = Document.query.find(dict(name='Foo')).first()
        assert d.content is None

    def test_delete_existing(self):
        doc = Document(name=u_('Foo2'))
        doc.content = open(self.fake_file.name, 'rb')
        DBSession.flush()
        DBSession.clear()


        d = Document.query.find(dict(name='Foo2')).first()
        old_file = d.content.path
        d.query.delete()

        DBSession.flush()
        DBSession.clear()

        try:
            fold = get_file(old_file)
            assert False, 'Should have raised IOError here'
        except IOError:
            pass

    def test_delete_existing_rollback(self):
        doc = Document(name=u_('Foo3'))
        doc.content = open(self.fake_file.name, 'rb')
        DBSession.flush()
        DBSession.clear()


        d = Document.query.find(dict(name='Foo3')).first()
        old_file = d.content.path
        d.delete()
        DBSession.clear()

        assert get_file(old_file).read() == self.file_content


class TestMingImageAttachments(object):
    def __init__(self):
        self.file_content = b'''R0lGODlhEQAUAPcAAC4uLjAwMDIyMjMzMjQ0NDU1NDY2Njk2Mzg4ODo6Oj49Ozw8PD4+PkE+OEA/PkhAN0tCNk5JPFFGNV1KMFhNNVFHOFJJPVVLPVhOPXZfKXVcK2ZQNGZXNGtZMnNcNHZeNnldMHJfOn1hKXVjOH9oO0BAQEJCQkREREVFREZGRklGQ05KQ0hISEpKSkxMTE5OTlZRSlFQT19XSFBQUFJSUlRUVGFUQmFVQ2ZZQGtdQnNiQqJ/HI1uIYBnLIllKoZrK4FqLoVqL4luLIpsLpt7J515JJ50KZhzLYFnMIFlM4ZlMIFkNI1uNoJoOoVrPIlvO49yMolwPpB2O5p4Op98PaB3IKN4JqN8J6h7I6J5LaZ+LLF+ILGGG7+JG72OGLKEI7aHIrOEJL2JI7mMN76YNcGJG8SOG8WLHMONH86eEs+aFsGSG8eQHMySG9uVFduXFdeeE9eaFdScF96YE9yaFOKcEuOdEtWgFNiiEduhE96pEuqlD+qmD+KpD+yoDu6rDuysDvCuDfCvDeuwD/SzC/a2CvGwDfKxDPi5Cfi5Cvq8CeCjEuehEOagEeijEOKoEOStFMOOK8+TLM6YNNChItGgLtylKt6gMNqgON6jPOChLfi/JOSrNeGvN9KhRtykRNWkSOCnQOCpSOawQue1T+a6Su67SOGsUO/AVAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACH5BAAAAAAALAAAAAARABQAAAj+AAEIHEiwoMAACBMqXIhQgMOHDwdAfEigYsUCT6KQScNjxwGLBAyINPBhCilUmxIV6uMlw0gEMJeMGWWqFCU8hA4JEgETQYIEDcRw6qRlwgMIGvJwkfAzwYIFXQBB8qHg6VMKFawuYNBBjaIqDhhI+cGgrNmyJXooGrShBJBKcIpwiFCibl0TehDdsWBCiBxLZuIwolMGiwcTJ4gUenThBAokSVRgGFJnzhYQJ1KsyRkkhWfPK87McWPEM4sRhgItCsGitQ5PmtxYUdK6BY4rf/zwYRNmUihRpyQdaUHchQsoX/Y4amTnUqZPoG7YMO7ihfUcYNC0eRMJExMqMKweW59BfkYMEk2ykHAio3x5GvDjy58Pv4b9+/jz2w8IADs='''
        self.file_content = base64.b64decode(self.file_content)
        self.fake_file = tempfile.NamedTemporaryFile()
        self.fake_file.write(self.file_content)
        self.fake_file.flush()

    def setup(self):
        clear_database()
        self.fake_file.seek(0)

    def test_create_fromfile(self):
        doc = Document(name=u_('Foo'))
        doc.photo = open(self.fake_file.name, 'rb')
        DBSession.flush()
        DBSession.clear()

        d = Document.query.find(dict(name='Foo')).first()
        assert d.photo.file.read() == self.file_content
        assert d.photo.filename == os.path.basename(self.fake_file.name)

    def test_create_fromfield(self):
        field = cgi.FieldStorage()
        field.filename = u_('àèìòù.gif')
        field.file = open(self.fake_file.name, 'rb')

        doc = Document(name=u_('Foo'), photo=field)
        DBSession.flush()
        DBSession.clear()

        d = Document.query.find(dict(name='Foo')).first()
        assert d.photo.file.read() == self.file_content
        assert d.photo.filename == field.filename
        assert d.photo.url == '/depot/%s' % d.photo.path
        assert d.photo.thumb_url == '/depot/%s' % d.photo.thumb_path
        assert d.photo.url != d.photo.thumb_url

    def test_thumbnail(self):
        field = create_cgifs('image/gif', self.fake_file, 'test.gif')

        doc = Document(name=u_('Foo'), photo=field)
        DBSession.flush()
        DBSession.clear()

        d = Document.query.find(dict(name='Foo')).first()
        assert os.path.exists(d.photo.thumb_file._file_path)

        thumb = Image.open(d.photo.thumb_file._file_path)
        thumb.verify()
        assert thumb.format.upper() == d.photo.thumbnail_format.upper()

    def test_public_url(self):
        doc = Document(name=u_('Foo'))
        doc.photo = open(self.fake_file.name, 'rb')
        doc.content = open(self.fake_file.name, 'rb')
        DBSession.flush()
        DBSession.clear()

        d = Document.query.find(dict(name='Foo')).first()

        # This is to edit the saved data bypassing UploadedFileProperty
        photo = FieldProperty(Field('photo', s.Anything)).__get__(d, Document)
        photo['_public_url'] = 'PUBLIC_URL'
        photo['_thumb_public_url'] = 'THUMB_PUBLIC_URL'

        # Now check that depot does the right thing when public urls are available
        assert d.photo.url == 'PUBLIC_URL'
        assert d.photo.thumb_url == 'THUMB_PUBLIC_URL'

    def test_rollback(self):
        raise SkipTest("Currently Ming Doesn't provide a way to handle discarded documents")

        doc = Document(name=u_('Foo3'))
        doc.photo = open(self.fake_file.name, 'rb')

        uploaded_file = doc.photo.path
        uploaded_thumb = doc.photo.thumb_path

        DBSession.clear()

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


class TestMingThumbnailFilter(object):
    def __init__(self):
        self.file_content = b'''R0lGODlhEQAUAPcAAC4uLjAwMDIyMjMzMjQ0NDU1NDY2Njk2Mzg4ODo6Oj49Ozw8PD4+PkE+OEA/PkhAN0tCNk5JPFFGNV1KMFhNNVFHOFJJPVVLPVhOPXZfKXVcK2ZQNGZXNGtZMnNcNHZeNnldMHJfOn1hKXVjOH9oO0BAQEJCQkREREVFREZGRklGQ05KQ0hISEpKSkxMTE5OTlZRSlFQT19XSFBQUFJSUlRUVGFUQmFVQ2ZZQGtdQnNiQqJ/HI1uIYBnLIllKoZrK4FqLoVqL4luLIpsLpt7J515JJ50KZhzLYFnMIFlM4ZlMIFkNI1uNoJoOoVrPIlvO49yMolwPpB2O5p4Op98PaB3IKN4JqN8J6h7I6J5LaZ+LLF+ILGGG7+JG72OGLKEI7aHIrOEJL2JI7mMN76YNcGJG8SOG8WLHMONH86eEs+aFsGSG8eQHMySG9uVFduXFdeeE9eaFdScF96YE9yaFOKcEuOdEtWgFNiiEduhE96pEuqlD+qmD+KpD+yoDu6rDuysDvCuDfCvDeuwD/SzC/a2CvGwDfKxDPi5Cfi5Cvq8CeCjEuehEOagEeijEOKoEOStFMOOK8+TLM6YNNChItGgLtylKt6gMNqgON6jPOChLfi/JOSrNeGvN9KhRtykRNWkSOCnQOCpSOawQue1T+a6Su67SOGsUO/AVAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACH5BAAAAAAALAAAAAARABQAAAj+AAEIHEiwoMAACBMqXIhQgMOHDwdAfEigYsUCT6KQScNjxwGLBAyINPBhCilUmxIV6uMlw0gEMJeMGWWqFCU8hA4JEgETQYIEDcRw6qRlwgMIGvJwkfAzwYIFXQBB8qHg6VMKFawuYNBBjaIqDhhI+cGgrNmyJXooGrShBJBKcIpwiFCibl0TehDdsWBCiBxLZuIwolMGiwcTJ4gUenThBAokSVRgGFJnzhYQJ1KsyRkkhWfPK87McWPEM4sRhgItCsGitQ5PmtxYUdK6BY4rf/zwYRNmUihRpyQdaUHchQsoX/Y4amTnUqZPoG7YMO7ihfUcYNC0eRMJExMqMKweW59BfkYMEk2ykHAio3x5GvDjy58Pv4b9+/jz2w8IADs='''
        self.file_content = base64.b64decode(self.file_content)
        self.fake_file = tempfile.NamedTemporaryFile()
        self.fake_file.write(self.file_content)
        self.fake_file.flush()

    def setup(self):
        clear_database()
        self.fake_file.seek(0)

    def test_create_fromfile(self):
        doc = Document(name=u_('Foo'))
        doc.second_photo = open(self.fake_file.name, 'rb')
        DBSession.flush()
        DBSession.clear()

        d = Document.query.find(dict(name='Foo')).first()
        assert d.second_photo.file.read() == self.file_content
        assert d.second_photo.filename == os.path.basename(self.fake_file.name)

    def test_create_fromfield(self):
        field = cgi.FieldStorage()
        field.filename = u_('àèìòù.gif')
        field.file = open(self.fake_file.name, 'rb')

        doc = Document(name=u_('Foo'), second_photo=field)
        DBSession.flush()
        DBSession.clear()

        d = Document.query.find(dict(name='Foo')).first()
        assert d.second_photo.file.read() == self.file_content
        assert d.second_photo.filename == field.filename
        assert d.second_photo.url == '/depot/%s' % d.second_photo.path
        assert d.second_photo.thumb_url == '/depot/%s' % d.second_photo.thumb_path
        assert d.second_photo.url != d.second_photo.thumb_url

    def test_thumbnail(self):
        field = create_cgifs('image/gif', self.fake_file, 'test.gif')

        doc = Document(name=u_('Foo'), second_photo=field)
        DBSession.flush()
        DBSession.clear()

        d = Document.query.find(dict(name='Foo')).first()
        thumbnail_local_path = DepotManager.get_file(d.second_photo.thumb_path)._file_path

        assert os.path.exists(thumbnail_local_path)

        thumb = Image.open(thumbnail_local_path)
        thumb.verify()
        assert thumb.format.upper() == 'PNG'
        assert max(thumb.size) == 12

    def test_public_url(self):
        doc = Document(name=u_('Foo'))
        doc.second_photo = open(self.fake_file.name, 'rb')
        doc.content = open(self.fake_file.name, 'rb')
        DBSession.flush()
        DBSession.clear()

        d = Document.query.find(dict(name='Foo')).first()

        # This is to edit the saved data bypassing UploadedFileProperty
        second_photo = FieldProperty(Field('second_photo', s.Anything)).__get__(d, Document)
        second_photo['_public_url'] = 'PUBLIC_URL'

        # Now check that depot does the right thing when public urls are available
        assert d.second_photo.url == 'PUBLIC_URL'
        assert d.second_photo.thumb_url.startswith('/depot/default/')

    def test_rollback(self):
        raise SkipTest("Currently Ming Doesn't provide a way to handle discarded documents")

        doc = Document(name=u_('Foo3'))
        doc.second_photo = open(self.fake_file.name, 'rb')

        uploaded_file = doc.second_photo.path
        uploaded_thumb = doc.second_photo.thumb_path

        DBSession.clear()

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