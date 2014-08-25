from __future__ import absolute_import

from ming.odm import mapper
from ming.odm.property import FieldProperty
from ming.odm.base import session, state, ObjectState
from ming.odm.odmsession import SessionExtension
from ming.schema import Anything

from depot.manager import DepotManager
from .upload import UploadedFile


class UploadedFileProperty(FieldProperty):
        def __init__(self,  filters=tuple(), upload_type=UploadedFile):
            FieldProperty.__init__(self, Anything())
            self._filters = filters
            self._upload_type = upload_type

        def __set__(self, instance, value):
            if value is not None and not isinstance(value, UploadedFile):
                upload_type = self._upload_type
                value = upload_type(value)

            if isinstance(value, UploadedFile):
                value._apply_filters(self._filters)

            old_value = self.__get__(instance, instance.__class__)
            DepotExtension.get_depot_history(instance).swap(old_value, value)
            return FieldProperty.__set__(self, instance, value)

        def __get__(self, instance, owner=None):
            try:
                value = FieldProperty.__get__(self, instance, owner)
            except AttributeError:
                value = None

            if not value:
                return None

            return self._upload_type(value)

        """
        # Looks like this should do nothing on ming.
        def __delete__(self, instance, owner=None):
            old_value = self.__get__(instance, instance.__class__)
            DepotExtension.get_depot_history(instance).delete(old_value)
            return FieldProperty.__delete__(self, instance, owner)
        """

class DepotExtension(SessionExtension):
    @classmethod
    def get_depot_history(cls, instance):
        istate = state(instance)
        if not hasattr(istate, '_depot_history'):
            istate._depot_history = _DepotHistory()
        return istate._depot_history

    def _check_object_deleted(self, obj):
        hist = self.get_depot_history(obj)
        if state(obj).status == ObjectState.deleted:
            for prop in mapper(obj).properties:
                if isinstance(prop, UploadedFileProperty):
                    current_value = prop.__get__(obj, obj.__class__)
                    hist.delete(current_value)
            self._flush_object(obj)

    def _flush_object(self, obj):
        history = self.get_depot_history(obj)
        for entry in history.deleted:
            depot, fileid = entry.split('/', 1)
            depot = DepotManager.get(depot)
            depot.delete(fileid)
        history.clear()

    def before_flush(self, obj=None):
        if obj:
            self._check_object_deleted(obj)
        else:
            for class_, id_, obj in self.session.imap:
                self._check_object_deleted(obj)

    def after_flush(self, obj=None):
        if obj:
            self._flush_object(obj)
        else:
            for class_, id_, obj in self.session.imap:
                self._flush_object(obj)


class _DepotHistory(object):
    def __init__(self):
        self.clear()

    def _extract_files(self, obj):
        return obj['files']

    def add(self, obj):
        if obj is None:
            return

        files = self._extract_files(obj)
        self.deleted.difference_update(obj)
        self.new.update(files)

    def delete(self, obj):
        if obj is None:
            return

        files = self._extract_files(obj)
        self.new.difference_update(obj)
        self.deleted.update(files)

    def swap(self, old, new):
        self.delete(old)
        self.add(new)

    def clear(self):
        self.deleted = set()
        self.new = set()
