from depot.io import utils
from depot.manager import DepotManager
from ..interfaces import FileFilter
from PIL import Image
from io import BytesIO


class WithThumbnailFilter(FileFilter):
    """Uploads a thumbnail together with the file.

    Takes for granted that the file is an image.
    The resulting uploaded file will provide three additional
    properties named:

        - ``thumb_X_id`` -> The depot file id
        - ``thumb_X_path`` -> Where the file is available in depot
        - ``thumb_X_url`` -> Where the file is served.

    Where ``X`` is the resolution specified as ``size`` in the
    filter initialization. By default this is ``(128, 128)``?so
    you will get ``thumb_128x128_id``, ``thumb_128x128_url`` and
    so on.

    .. warning::

        Requires Pillow library

    """
    def __init__(self, size=(128,128), format='PNG'):
        self.thumbnail_size = size
        self.thumbnail_format = format

    def on_save(self, uploaded_file):
        content = utils.file_from_content(uploaded_file.original_content)

        thumbnail = Image.open(content)
        thumbnail.thumbnail(self.thumbnail_size, Image.BILINEAR)
        thumbnail = thumbnail.convert('RGBA')
        thumbnail.format = self.thumbnail_format

        output = BytesIO()
        thumbnail.save(output, self.thumbnail_format)
        output.seek(0)

        thumb_name = 'thumb_%sx%s' % self.thumbnail_size
        thumb_file_name = '%s.%s' % (thumb_name, self.thumbnail_format.lower())
        thumb_path, thumb_id = uploaded_file.store_content(output, thumb_file_name)
        uploaded_file[thumb_name + '_id'] = thumb_id
        uploaded_file[thumb_name + '_path'] = thumb_path
        uploaded_file[thumb_name + '_url'] = DepotManager.get_middleware().url_for(thumb_path)

