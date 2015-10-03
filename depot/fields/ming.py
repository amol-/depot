from __future__ import absolute_import

from ming.odm import mapper
from ming.odm.property import FieldProperty
from ming.odm.base import session, state, ObjectState
from ming.odm.odmsession import SessionExtension
from ming.schema import Anything

from depot.manager import DepotManager
from .upload import UploadedFile


class _UploadedFileSchema(Anything):
    pass


class UploadedFileProperty(FieldProperty):
    """Provides support for storing attachments to **Ming** MongoDB models.

    ``UploadedFileProperty`` can be used as a field type to store files
    into the model. The actual file itself will be uploaded to the
    default Storage, and only the :class:`depot.fields.upload.UploadedFile`
    information will be stored on the database.

    The ``UploadedFileProperty`` is UnitOfWork aware, so it will delete
    every uploaded file whenever unit of work is flushed and deletes a Document
    that stored files or changes the field of a document storing files. This is
    the reason you should never associate the same :class:`depot.fields.upload.UploadedFile`
    to two different ``UploadedFileProperty``, otherwise you might delete a file
    already used by another document. It is usually best to just set the ``file``
    or ``bytes`` as content of the column and let the ``UploadedFileProperty``
    create the :class:`depot.fields.upload.UploadedFile` by itself whenever it's content is set.

    .. warning::

        As the Ming UnitOfWork does not notify any event in case it gets cleared instead
        of being flushed all the files uploaded before clearing the unit of work will be
        already uploaded but won't have a document referencing them anymore, so DEPOT will
        be unable to delete them for you.

    """
    def __init__(self,  filters=tuple(), upload_type=UploadedFile, upload_storage=None):
        FieldProperty.__init__(self, _UploadedFileSchema())
        self._filters = filters
        self._upload_type = upload_type
        self._upload_storage = upload_storage

    def __set__(self, instance, value):
        if value is not None and not isinstance(value, UploadedFile):
            upload_type = self._upload_type
            value = upload_type(value, self._upload_storage)

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

        if instance is None:
            return value

        return self._upload_type(value)

    """
    # Looks like this should do nothing on ming.
    def __delete__(self, instance, owner=None):
        old_value = self.__get__(instance, instance.__class__)
        DepotExtension.get_depot_history(instance).delete(old_value)
        return FieldProperty.__delete__(self, instance, owner)
    """


class DepotExtension(SessionExtension):
    """Extends the Ming Session to track files.

    Deletes old files when an entry gets removed or replaced,
    apply this as a Ming ``SessionExtension`` according to Ming
    documentation.
    """
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


try:  # pragma: no cover
    from sprox.mg.widgetselector import MingWidgetSelector
    from tw2.forms import FileField as TW2FileField
    MingWidgetSelector.default_widgets.setdefault(_UploadedFileSchema, TW2FileField)

    from sprox.mg.validatorselector import MingValidatorSelector
    from ..validators import TW2FileIntentValidator
    MingValidatorSelector.default_validators.setdefault(_UploadedFileSchema, TW2FileIntentValidator)
except ImportError:  # pragma: no cover
    pass