from __future__ import absolute_import
import sqlalchemy.types as types


class FileField(types.TypeDecorator):
    impl = types.Unicode

    def __init__(self, filters=tuple(), *args, **kw):
        super(FileField, self).__init__(*args, **kw)
        self._filters = filters

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(types.VARCHAR(4096))

    def process_bind_param(self, value, dialect):
        pass

    def process_result_value(self, value, dialect):
        if not value:
            return None

        pass


try:
    from sprox.sa.widgetselector import SAWidgetSelector
    from tw2.forms import FileField as TW2FileField
    SAWidgetSelector.default_widgets.setdefault(FileField, TW2FileField)

    from sprox.sa.validatorselector import SAValidatorSelector
    from tw2.forms import FileValidator
    SAValidatorSelector.default_validators.setdefault(FileField, FileValidator)
except ImportError:
    pass