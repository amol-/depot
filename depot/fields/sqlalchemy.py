from __future__ import absolute_import
import itertools

from sqlalchemy import types
from sqlalchemy import event
from sqlalchemy import orm
from sqlalchemy import inspect
from sqlalchemy.orm import ColumnProperty
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import get_history

from depot.manager import DepotManager
from .upload import UploadedFile


class UploadedFileField(types.TypeDecorator):
    """Provides support for storing attachments to **SQLAlchemy** models.

    ``UploadedFileField`` can be used as a Column type to store files
    into the model. The actual file itself will be uploaded to the
    default Storage, and only the :class:`depot.fields.upload.UploadedFile`
    information will be stored on the database.

    The ``UploadedFileField`` is transaction aware, so it will delete
    every uploaded file whenever the transaction is rolled back and will
    delete any old file whenever the transaction is committed. This is
    the reason you should never associate the same :class:`depot.fields.upload.UploadedFile`
    to two different ``UploadedFileField``, otherwise you might delete a file
    already used by another model. It is usually best to just set the ``file``
    or ``bytes`` as content of the column and let the ``UploadedFileField``
    create the :class:`depot.fields.upload.UploadedFile` by itself whenever it's content is set.

    """
    impl = types.Unicode

    def __init__(self, filters=tuple(), upload_type=UploadedFile, upload_storage=None, *args, **kw):
        super(UploadedFileField, self).__init__(*args, **kw)
        self._filters = filters
        self._upload_type = upload_type
        self._upload_storage = upload_storage

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(types.VARCHAR(4000))

    def process_bind_param(self, value, dialect):
        if not value:
            return None

        if not isinstance(value, self._upload_type):
            raise ValueError('AttachmentField requires %s, '
                             'got %s instead' % (self._upload_type, type(value)))

        return value.encode()

    def process_result_value(self, value, dialect):
        if not value:
            return None
        return self._upload_type.decode(value)


class _SQLAMutationTracker(object):
    mapped_entities = {}

    @classmethod
    def _field_set(cls, target, value, oldvalue, initiator):
        if value is None or isinstance(value, UploadedFile):
            return value

        inspection = inspect(target)
        set_property = inspection.mapper.get_property(initiator.key)
        column_type = set_property.columns[0].type
        assert(isinstance(column_type, UploadedFileField))

        upload_type = column_type._upload_type
        value = upload_type(value, column_type._upload_storage)
        value._apply_filters(column_type._filters)

        # Mark newly added files on assignment, so that in case of a rollback
        # without going through flush we have track of the files
        # that need to be rolled back.
        session = inspection.session
        if session is not None:
            session._depot_new = getattr(session, '_depot_new', set())
            session._depot_new.update(value.files)
        else:
            # If object is not attached to a session preserve the files
            # until it gets added to one.
            target._depot_new = getattr(target, '_depot_new', set())
            target._depot_new.update(value.files)

        return value

    @classmethod
    def _mapper_configured(cls, mapper, class_):
        for mapper_property in mapper.iterate_properties:
            if isinstance(mapper_property, ColumnProperty):
                for idx, col in enumerate(mapper_property.columns):
                    if isinstance(col.type, UploadedFileField):
                        if idx > 0:
                            # Not clear when this might happen, but ColumnProperty can have
                            # multiple columns assigned. We should probably take the first one
                            # as is done by ColumnProperty.expression but there is no guarantee
                            # that it would be the right thing to do.
                            raise TypeError('UploadedFileField currently supports a single column')
                        cls.mapped_entities.setdefault(class_, []).append(mapper_property.key)
                        event.listen(mapper_property, 'set', cls._field_set, retval=True, propagate=True)

    @classmethod
    def _session_rollback(cls, session, previous_transaction):
        if hasattr(session, '_depot_old'):
            del session._depot_old
        if hasattr(session, '_depot_new'):
            for entry in session._depot_new:
                depot, fileid = entry.split('/', 1)
                depot = DepotManager.get(depot)
                depot.delete(fileid)
            del session._depot_new

    @classmethod
    def _session_committed(cls, session):
        if hasattr(session, '_depot_old'):
            for entry in session._depot_old:
                depot, fileid = entry.split('/', 1)
                depot = DepotManager.get(depot)
                depot.delete(fileid)
            del session._depot_old
        if hasattr(session, '_depot_new'):
            del session._depot_new

    @classmethod
    def _session_flush(cls, session, flush_context, instances):
        for obj in session.deleted:
            class_ = obj.__class__
            tracked_columns = cls.mapped_entities.get(class_, tuple())
            for col in tracked_columns:
                value = getattr(obj, col)
                if value is not None:
                    session._depot_old = getattr(session, '_depot_old', set())
                    session._depot_old.update(value.files)

        for obj in session.new.union(session.dirty):
            class_ = obj.__class__
            tracked_columns = cls.mapped_entities.get(class_, tuple())
            for col in tracked_columns:
                history = get_history(obj, col)
                added_files = itertools.chain(*(f.files for f in history.added
                                               if f is not None))
                deleted_files = itertools.chain(*(f.files for f in history.deleted
                                                 if f is not None))

                session._depot_new = getattr(session, '_depot_new', set())
                session._depot_new.update(added_files)
                session._depot_old = getattr(session, '_depot_old', set())
                session._depot_old.update(deleted_files)

    @classmethod
    def _session_after_flush(cls, session, flush_context):
        # Tracking deleted object _after_ flush
        # is the way we can track for objects deleted through
        # a relationship.remove, because those only get
        # deleted _after_ the session was flushed. Not before.
        for state in flush_context.states.keys():
            if not state.deleted:
                continue
            obj = state.obj()
            class_ = obj.__class__
            tracked_columns = cls.mapped_entities.get(class_, tuple())
            for col in tracked_columns:
                value = getattr(obj, col)
                if value is not None:
                    session._depot_old = getattr(session, '_depot_old', set())
                    session._depot_old.update(value.files)

    @classmethod
    def _session_attached(cls, session, instance):
        session._depot_new = getattr(session, '_depot_new', set())
        session._depot_new.update(getattr(instance, '_depot_new', set()))

    @classmethod
    def setup(cls):
        event.listen(orm.mapper, 'mapper_configured', cls._mapper_configured)
        event.listen(Session, 'after_soft_rollback', cls._session_rollback)
        event.listen(Session, 'after_commit', cls._session_committed)
        event.listen(Session, 'before_attach', cls._session_attached)
        event.listen(Session, 'before_flush', cls._session_flush)
        event.listen(Session, 'after_flush_postexec', cls._session_after_flush)

_SQLAMutationTracker.setup()

try:  # pragma: no cover
    from sprox.sa.widgetselector import SAWidgetSelector
    from tw2.forms import FileField as TW2FileField
    SAWidgetSelector.default_widgets.setdefault(UploadedFileField, TW2FileField)

    from sprox.sa.validatorselector import SAValidatorSelector
    from ..validators import TW2FileIntentValidator
    SAValidatorSelector.default_validators.setdefault(UploadedFileField, TW2FileIntentValidator)
except ImportError:  # pragma: no cover
    pass