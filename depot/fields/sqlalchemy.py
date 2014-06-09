from __future__ import absolute_import
import sqlalchemy.types as types
from depot.manager import get_depot
from .utils import FileInfo


class FileField(types.TypeDecorator):
    impl = types.Unicode

    def __init__(self, filters=tuple(), depot=None, *args, **kw):
        super(FileField, self).__init__(*args, **kw)
        self._filters = filters
        self._depot = depot

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(types.VARCHAR(4096))

    def process_bind_param(self, value, dialect):
        for filt in self._filters:
            value = filt.before_save(value)

        data = {}
        f = get_depot(self._depot)
        data['file_id'] = f
        data['path'] = '%s/%s' % (self._depot, f)
        return FileInfo.marshall(data)

    def process_result_value(self, value, dialect):
        if not value:
            return None
        return FileInfo(value)


try:
    from sprox.sa.widgetselector import SAWidgetSelector
    from tw2.forms import FileField as TW2FileField
    SAWidgetSelector.default_widgets.setdefault(FileField, TW2FileField)

    from sprox.sa.validatorselector import SAValidatorSelector
    from tw2.forms import FileValidator
    SAValidatorSelector.default_validators.setdefault(FileField, FileValidator)
except ImportError:
    pass