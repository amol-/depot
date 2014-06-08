from .interfaces import FileFilter
from PIL import Image
from io import BytesIO
from depot.manager import get_depot


class Image(FileFilter):
    def __int__(self, thumbnail_size):
        self.thumbnail_format = 'PNG'
        self.thumbnail_size = thumbnail_size

    def after_save(self, content, field_data):
        depot = get_depot(field_data['depot'])

        thumbnail = Image.open(self.content_file(content))
        thumbnail.thumbnail(self.thumbnail_size, Image.BILINEAR)
        thumbnail = thumbnail.convert('RGBA')
        thumbnail.format = self.thumbnail_format

        output = BytesIO()
        thumbnail.save(output)
        thumbnail.close()

        thumb_id = depot.create(output,
                                'thumb.%s' % self.thumbnail_format.lower())
        field_data['thumbnail'] = thumb_id
        field_data['thumb_path'] = '%s/%s' % (field_data['depot'], thumb_id)



