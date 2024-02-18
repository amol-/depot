# -*- coding: utf-8 -*-
import shutil
import tempfile, os, base64
import unittest
from sqlalchemy.schema import Column
from sqlalchemy.types import Unicode, Integer
from .base_sqla import setup_database, clear_database, DeclarativeBase, DBSession
from depot.fields.sqlalchemy import UploadedFileField
from depot.fields.upload import UploadedFile
from depot.manager import DepotManager
from depot.fields.interfaces import FileFilter

from depot._compat import u_, bytes_

def setUpModule():
    setup_database()

    DepotManager._clear()
    DepotManager.configure('default', {'depot.storage_path': './lfs'})


def tearDownModule():
    shutil.rmtree('./lfs', ignore_errors=True)


class DictLikeCheckFilter(FileFilter):
    def on_save(self, uploaded_file):
        uploaded_file['changed'] = 'OLD'
        uploaded_file['hello'] = 'World'
        uploaded_file['deleted'] = False
        del uploaded_file['deleted']
        uploaded_file['changed'] = 'NEW'
        uploaded_file['deleted_attr'] = False
        del uploaded_file.deleted_attr

        try:
            del uploaded_file.missing_attr
        except AttributeError:
            uploaded_file.missing_attr_trapped = True


class SimpleDocument(DeclarativeBase):
    __tablename__ = 'simple_docu'

    uid = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(Unicode(16), unique=True)
    content = Column('content_col', UploadedFileField([DictLikeCheckFilter()]))


class TestFieldsInterface(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.file_content = b'this is the file content'
        cls.fake_file = tempfile.NamedTemporaryFile()
        cls.fake_file.write(cls.file_content)
        cls.fake_file.flush()

    @classmethod
    def tearDownClass(cls):
        cls.fake_file.close()

    def setUp(self):
        clear_database()

    def test_column_is_dictlike(self):
        doc = SimpleDocument(name=u_('Foo'))
        doc.content = open(self.fake_file.name, 'rb')
        DBSession.add(doc)
        DBSession.flush()
        DBSession.commit()

        d = DBSession.query(SimpleDocument).filter_by(name=u_('Foo')).first()
        assert doc.content.hello == 'World', doc.content
        assert 'deleted' not in doc.content, doc.content
        assert doc.content.changed == 'NEW', doc.content
        assert 'deleted_attr' not in doc.content, doc.content
        assert doc.content.missing_attr_trapped == True, doc.content

    def test_column_cannot_edit_after_save(self):
        doc = SimpleDocument(name=u_('Foo'))
        doc.content = open(self.fake_file.name, 'rb')
        DBSession.add(doc)
        DBSession.flush()
        DBSession.commit()

        d = DBSession.query(SimpleDocument).filter_by(name=u_('Foo')).first()
        with self.assertRaises(TypeError):
            d.content['hello'] = 'Everybody'

    def test_column_cannot_delete_after_save(self):
        doc = SimpleDocument(name=u_('Foo'))
        doc.content = open(self.fake_file.name, 'rb')
        DBSession.add(doc)
        DBSession.flush()
        DBSession.commit()

        d = DBSession.query(SimpleDocument).filter_by(name=u_('Foo')).first()
        with self.assertRaises(TypeError):
            del d.content['hello']

    def test_column_cannot_edit_attr_after_save(self):
        doc = SimpleDocument(name=u_('Foo'))
        doc.content = open(self.fake_file.name, 'rb')
        DBSession.add(doc)
        DBSession.flush()
        DBSession.commit()

        d = DBSession.query(SimpleDocument).filter_by(name=u_('Foo')).first()
        with self.assertRaises(TypeError):
            d.content.hello = 'Everybody'

    def test_column_cannot_delete_attr_after_save(self):
        doc = SimpleDocument(name=u_('Foo'))
        doc.content = open(self.fake_file.name, 'rb')
        DBSession.add(doc)
        DBSession.flush()
        DBSession.commit()

        d = DBSession.query(SimpleDocument).filter_by(name=u_('Foo')).first()
        with self.assertRaises(TypeError):
            del d.content.hello

    def test_storage_does_not_exists(self):
        doc = SimpleDocument(name=u_('Foo'))
        with self.assertRaises(ValueError):
            doc.content = UploadedFile(open(self.fake_file.name, 'rb'),
                                    'missing_storage')
        DBSession.add(doc)
        DBSession.flush()
        DBSession.commit()
