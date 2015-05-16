import cgi
from depot.io.utils import FileIntent
from depot.io.interfaces import FileStorage

__all__ = ('TW2FileIntentValidator', )

try:
    import tw2.core
except ImportError:
    pass
else:
    class TW2FileIntentValidator(tw2.core.Validator):
        """Validator for ToscaWidgets2

        Converts the uploaded file to a DEPOT FileIntent
        so that it preserves file details like filename
        and content type when uploaded. This is mostly
        required when working with Sprox that converts
        the cgi.FieldStorage to a standard BLOB when
        handling uploaded files, causing a loss of all
        file metadata.
        """
        extension = None
        msgs = {
            'required': ('file_required', 'Select a file'),
            'badext': "File name must have '$extension' extension",
        }

        def _convert_to_python(self, value, state=None):
            if isinstance(value, cgi.FieldStorage):
                if self.required and not getattr(value, 'filename', None):
                    raise tw2.core.ValidationError('required', self)

                if (self.extension is not None
                        and not value.filename.endswith(self.extension)):
                    raise tw2.core.ValidationError('badext', self)
            elif value:
                raise tw2.core.ValidationError('corrupt', self)
            elif self.required:
                raise tw2.core.ValidationError('required', self)

            return FileIntent(*FileStorage.fileinfo(value))
