# -*- coding: utf-8 -*-
import shutil

import tempfile, os, cgi, base64
from PIL import Image
from nose.tools import raises
from sqlalchemy.exc import StatementError
from sqlalchemy.schema import Column
from sqlalchemy.types import Unicode, Integer
from .base_sqla import setup_database, clear_database, DeclarativeBase, DBSession
from depot.fields.sqlalchemy import UploadedFileField
from depot.fields.upload import UploadedFile
from depot.manager import DepotManager, get_file
from .utils import create_cgifs
from depot.fields.specialized.image import UploadedImageWithThumb
from depot.fields.filters.thumbnails import WithThumbnailFilter
from depot._compat import u_, bytes_

def setup():
    setup_database()

    DepotManager._clear()
    DepotManager.configure('default', {'depot.storage_path': './lfs'})
    DepotManager.make_middleware(None)


def teardown():
    shutil.rmtree('./lfs', ignore_errors=True)




class Document(DeclarativeBase):
    __tablename__ = 'docu'

    uid = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(Unicode(16), unique=True)
    content = Column('content_col', UploadedFileField)
    photo = Column(UploadedFileField(upload_type=UploadedImageWithThumb))
    second_photo = Column(UploadedFileField(filters=(WithThumbnailFilter((12, 12), 'PNG'),)))


class TestSQLAAttachments(object):
    def __init__(self):
        self.file_content = b'this is the file content'
        self.fake_file = tempfile.NamedTemporaryFile()
        self.fake_file.write(self.file_content)
        self.fake_file.flush()

    def setup(self):
        clear_database()

    def test_create_fromfile(self):
        doc = Document(name=u_('Foo'))
        doc.content = open(self.fake_file.name, 'rb')
        DBSession.add(doc)
        DBSession.flush()
        DBSession.commit()

        d = DBSession.query(Document).filter_by(name=u_('Foo')).first()
        assert d.content.file.read() == self.file_content
        assert d.content.file.filename == os.path.basename(self.fake_file.name)

    def test_edit_existing(self):
        doc = Document(name=u_('Foo2'))
        doc.content = open(self.fake_file.name, 'rb')
        DBSession.add(doc)
        DBSession.flush()
        DBSession.commit()
        DBSession.remove()

        d = DBSession.query(Document).filter_by(name=u_('Foo2')).first()
        old_file =  d.content.path

        d.content = b'HELLO'
        new_file = d.content.path

        DBSession.flush()
        DBSession.commit()
        DBSession.remove()

        assert get_file(new_file).read() == b'HELLO'

        try:
            fold = get_file(old_file)
            assert False, 'Should have raised IOError here'
        except IOError:
            pass

    def test_edit_existing_rollback(self):
        doc = Document(name=u_('Foo3'))
        doc.content = open(self.fake_file.name, 'rb')
        DBSession.add(doc)
        DBSession.flush()
        DBSession.commit()
        DBSession.remove()

        d = DBSession.query(Document).filter_by(name=u_('Foo3')).first()
        old_file = d.content.path

        d.content = b'HELLO'
        new_file = d.content.path

        DBSession.flush()
        DBSession.rollback()
        DBSession.remove()

        assert get_file(old_file).read() == self.file_content

        try:
            fold = get_file(new_file)
            assert False, 'Should have raised IOError here'
        except IOError:
            pass

    def test_create_fromfield(self):
        field = create_cgifs('image/jpeg', self.fake_file, 'test.jpg')

        doc = Document(name=u_('Foo'), content=field)
        DBSession.add(doc)
        DBSession.flush()
        DBSession.commit()

        d = DBSession.query(Document).filter_by(name=u_('Foo')).first()
        assert d.content.file.read() == self.file_content
        assert d.content.filename == 'test.jpg'
        assert d.content.content_type == 'image/jpeg', d.content.content_type
        assert d.content.url == '/depot/%s' % d.content.path

    def test_create_empty(self):
        doc = Document(name=u_('Foo'), content=None)
        DBSession.add(doc)
        DBSession.flush()
        DBSession.commit()

        d = DBSession.query(Document).filter_by(name=u_('Foo')).first()
        assert d.content is None

    def test_delete_existing(self):
        doc = Document(name=u_('Foo2'))
        doc.content = open(self.fake_file.name, 'rb')
        DBSession.add(doc)
        DBSession.flush()
        DBSession.commit()
        DBSession.remove()

        d = DBSession.query(Document).filter_by(name=u_('Foo2')).first()
        old_file = d.content.path
        DBSession.delete(d)

        DBSession.flush()
        DBSession.commit()
        DBSession.remove()

        try:
            fold = get_file(old_file)
            assert False, 'Should have raised IOError here'
        except IOError:
            pass

    def test_delete_existing_rollback(self):
        doc = Document(name=u_('Foo3'))
        doc.content = open(self.fake_file.name, 'rb')
        DBSession.add(doc)
        DBSession.flush()
        DBSession.commit()
        DBSession.remove()

        d = DBSession.query(Document).filter_by(name=u_('Foo3')).first()
        old_file = d.content.path
        DBSession.delete(d)

        DBSession.flush()
        DBSession.rollback()
        DBSession.remove()

        assert get_file(old_file).read() == self.file_content


class TestSQLAImageAttachments(object):
    def __init__(self):
        self.file_content = b'''R0lGODlhEQAUAPcAAC4uLjAwMDIyMjMzMjQ0NDU1NDY2Njk2Mzg4ODo6Oj49Ozw8PD4+PkE+OEA/PkhAN0tCNk5JPFFGNV1KMFhNNVFHOFJJPVVLPVhOPXZfKXVcK2ZQNGZXNGtZMnNcNHZeNnldMHJfOn1hKXVjOH9oO0BAQEJCQkREREVFREZGRklGQ05KQ0hISEpKSkxMTE5OTlZRSlFQT19XSFBQUFJSUlRUVGFUQmFVQ2ZZQGtdQnNiQqJ/HI1uIYBnLIllKoZrK4FqLoVqL4luLIpsLpt7J515JJ50KZhzLYFnMIFlM4ZlMIFkNI1uNoJoOoVrPIlvO49yMolwPpB2O5p4Op98PaB3IKN4JqN8J6h7I6J5LaZ+LLF+ILGGG7+JG72OGLKEI7aHIrOEJL2JI7mMN76YNcGJG8SOG8WLHMONH86eEs+aFsGSG8eQHMySG9uVFduXFdeeE9eaFdScF96YE9yaFOKcEuOdEtWgFNiiEduhE96pEuqlD+qmD+KpD+yoDu6rDuysDvCuDfCvDeuwD/SzC/a2CvGwDfKxDPi5Cfi5Cvq8CeCjEuehEOagEeijEOKoEOStFMOOK8+TLM6YNNChItGgLtylKt6gMNqgON6jPOChLfi/JOSrNeGvN9KhRtykRNWkSOCnQOCpSOawQue1T+a6Su67SOGsUO/AVAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACH5BAAAAAAALAAAAAARABQAAAj+AAEIHEiwoMAACBMqXIhQgMOHDwdAfEigYsUCT6KQScNjxwGLBAyINPBhCilUmxIV6uMlw0gEMJeMGWWqFCU8hA4JEgETQYIEDcRw6qRlwgMIGvJwkfAzwYIFXQBB8qHg6VMKFawuYNBBjaIqDhhI+cGgrNmyJXooGrShBJBKcIpwiFCibl0TehDdsWBCiBxLZuIwolMGiwcTJ4gUenThBAokSVRgGFJnzhYQJ1KsyRkkhWfPK87McWPEM4sRhgItCsGitQ5PmtxYUdK6BY4rf/zwYRNmUihRpyQdaUHchQsoX/Y4amTnUqZPoG7YMO7ihfUcYNC0eRMJExMqMKweW59BfkYMEk2ykHAio3x5GvDjy58Pv4b9+/jz2w8IADs='''
        self.file_content = base64.b64decode(self.file_content)
        self.fake_file = tempfile.NamedTemporaryFile()
        self.fake_file.write(self.file_content)
        self.fake_file.flush()

        self.bigimage = tempfile.NamedTemporaryFile()
        blackimage = Image.frombytes('L', (1280, 1280), b"\x00" * 1280 * 1280)
        blackimage.save(self.bigimage, 'PNG')
        self.bigimage.flush()

    def setup(self):
        clear_database()
        self.fake_file.seek(0)

    def test_create_fromfile(self):
        doc = Document(name=u_('Foo'))
        doc.photo = open(self.fake_file.name, 'rb')
        DBSession.add(doc)
        DBSession.flush()
        DBSession.commit()

        d = DBSession.query(Document).filter_by(name=u_('Foo')).first()
        assert d.photo.file.read() == self.file_content
        assert d.photo.filename == os.path.basename(self.fake_file.name)

    def test_check_assigned_type(self):
        doc = Document(name=u_('Foo'))
        doc.photo = UploadedFile(open(self.fake_file.name, 'rb'))
        DBSession.add(doc)

        try:
            DBSession.flush()
        except StatementError as e:
            assert 'ValueError' in str(e)
            return

        assert False, 'FLUSH did not raise exception'

    def test_create_fromfield(self):
        field = cgi.FieldStorage()
        field.filename = u_('àèìòù.gif')
        field.file = open(self.fake_file.name, 'rb')

        doc = Document(name=u_('Foo'), photo=field)
        DBSession.add(doc)
        DBSession.flush()
        DBSession.commit()

        d = DBSession.query(Document).filter_by(name=u_('Foo')).first()
        assert d.photo.file.read() == self.file_content
        assert d.photo.filename == field.filename
        assert d.photo.url == '/depot/%s' % d.photo.path
        assert d.photo.thumb_url == '/depot/%s' % d.photo.thumb_path
        assert d.photo.url != d.photo.thumb_url

    def test_thumbnail(self):
        field = create_cgifs('image/gif', self.fake_file, 'test.gif')

        doc = Document(name=u_('Foo'), photo=field)
        DBSession.add(doc)
        DBSession.flush()
        DBSession.commit()

        d = DBSession.query(Document).filter_by(name=u_('Foo')).first()
        assert os.path.exists(d.photo.thumb_file._file_path)

        thumb = Image.open(d.photo.thumb_file._file_path)
        thumb.verify()
        assert thumb.format.upper() == d.photo.thumbnail_format.upper()

    def test_maximum_size(self):
        field = create_cgifs('image/png', self.bigimage, 'test.png')

        doc = Document(name=u_('Foo'), photo=field)
        DBSession.add(doc)
        DBSession.flush()
        DBSession.commit()

        d = DBSession.query(Document).filter_by(name=u_('Foo')).first()

        img = Image.open(d.photo.file._file_path)
        img.verify()
        assert img.format.upper() == 'PNG'
        assert max(img.size) == 1024
        assert d.photo.filename == field.filename
        assert d.photo.content_type == 'image/png'

    def test_public_url(self):
        doc = Document(name=u_('Foo'))
        doc.photo = open(self.fake_file.name, 'rb')
        doc.content = open(self.fake_file.name, 'rb')
        DBSession.add(doc)
        DBSession.flush()
        DBSession.commit()

        d = DBSession.query(Document).filter_by(name=u_('Foo')).first()

        # Hack to force object to have a public url
        d.photo._thaw()
        d.photo['_public_url'] = 'PUBLIC_URL'
        d.photo['_thumb_public_url'] = 'THUMB_PUBLIC_URL'
        d.photo._freeze()

        assert d.photo.url == 'PUBLIC_URL'
        assert d.photo.thumb_url == 'THUMB_PUBLIC_URL'

    def test_rollback(self):
        doc = Document(name=u_('Foo3'))
        doc.photo = open(self.fake_file.name, 'rb')
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


class TestSQLAThumbnailFilter(object):
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
        DBSession.add(doc)
        DBSession.flush()
        DBSession.commit()

        d = DBSession.query(Document).filter_by(name=u_('Foo')).first()
        assert d.second_photo.file.read() == self.file_content
        assert d.second_photo.filename == os.path.basename(self.fake_file.name)

    def test_create_from_bytes(self):
        doc = Document(name=u_('Foo'))
        doc.second_photo = self.file_content
        DBSession.add(doc)
        DBSession.flush()
        DBSession.commit()

        d = DBSession.query(Document).filter_by(name=u_('Foo')).first()
        assert d.second_photo.file.read() == self.file_content
        assert d.second_photo.filename == 'unknown'

    def test_create_fromfield(self):
        field = cgi.FieldStorage()
        field.filename = u_('àèìòù.gif')
        field.file = open(self.fake_file.name, 'rb')

        doc = Document(name=u_('Foo'), second_photo=field)
        DBSession.add(doc)
        DBSession.flush()
        DBSession.commit()

        d = DBSession.query(Document).filter_by(name=u_('Foo')).first()
        assert d.second_photo.file.read() == self.file_content
        assert d.second_photo.filename == field.filename
        assert d.second_photo.url == '/depot/%s' % d.second_photo.path
        assert d.second_photo.thumb_url == '/depot/%s' % d.second_photo.thumb_path
        assert d.second_photo.url != d.second_photo.thumb_url

    def test_thumbnail(self):
        field = create_cgifs('image/gif', self.fake_file, 'test.gif')

        doc = Document(name=u_('Foo'), second_photo=field)
        DBSession.add(doc)
        DBSession.flush()
        DBSession.commit()

        d = DBSession.query(Document).filter_by(name=u_('Foo')).first()

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
        DBSession.add(doc)
        DBSession.flush()
        DBSession.commit()

        d = DBSession.query(Document).filter_by(name=u_('Foo')).first()

        # Hack to force object to have a public url
        d.second_photo._thaw()
        d.second_photo['_public_url'] = 'PUBLIC_URL'
        d.second_photo._freeze()

        assert d.second_photo.url == 'PUBLIC_URL'
        assert d.second_photo.thumb_url.startswith('/depot/default/')

    def test_rollback(self):
        doc = Document(name=u_('Foo3'))
        doc.second_photo = open(self.fake_file.name, 'rb')
        DBSession.add(doc)
        DBSession.flush()

        uploaded_file = doc.second_photo.path
        uploaded_thumb = doc.second_photo.thumb_path

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
