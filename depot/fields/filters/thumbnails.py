from depot.io import utils
from depot.manager import DepotManager
from ..interfaces import FileFilter
from PIL import Image
from io import BytesIO


class WithThumbnailFilter(FileFilter):
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

        thumb_file_name = 'thumb.%s' % self.thumbnail_format.lower()
        thumb_path, thumb_id = uploaded_file.store_content(output, thumb_file_name)
        uploaded_file['thumb_id'] = thumb_id
        uploaded_file['thumb_path'] = thumb_path
        uploaded_file['thumb_url'] = DepotManager.get_middleware().url_for(thumb_path)


