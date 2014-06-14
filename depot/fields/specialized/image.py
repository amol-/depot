from depot.io import utils
from depot.manager import DepotManager
from ..upload import UploadedFile
from PIL import Image
from io import BytesIO


class UploadedImageWithThumb(UploadedFile):
    """Uploads an Image with thumbnail.

    The default thumbnail format and size are PNG@128x128, those can be changed
    by inheriting the ``UploadedImageWithThumb`` and replacing the
    ``thumbnail_format`` and ``thumbnail_size`` class properties.

    The Thumbnail file is accessible as ``.thumb_file`` while the
    thumbnail url is ``.thumb_url``.

    """

    thumbnail_format = 'PNG'
    thumbnail_size = (128, 128)

    def process_content(self, content):
        super(UploadedImageWithThumb, self).process_content(content)

        content = utils.file_from_content(content)
        thumbnail = Image.open(content)
        thumbnail.thumbnail(self.thumbnail_size, Image.BILINEAR)
        thumbnail = thumbnail.convert('RGBA')
        thumbnail.format = self.thumbnail_format

        output = BytesIO()
        thumbnail.save(output, self.thumbnail_format)
        output.seek(0)

        thumb_path, thumb_id = self.store_content(output,
                                                  'thumb.%s' % self.thumbnail_format.lower())
        self['thumb_id'] = thumb_id
        self['thumb_path'] = thumb_path

        thumbnail_file = self.thumb_file
        self['_thumb_public_url'] = thumbnail_file.public_url

    @property
    def thumb_file(self):
        return self.depot.get(self.thumb_id)

    @property
    def thumb_url(self):
        public_url = self['_thumb_public_url']
        if public_url:
            return public_url
        return DepotManager.get_middleware().url_for(self['thumb_path'])
