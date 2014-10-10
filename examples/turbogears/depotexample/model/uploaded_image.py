# -*- coding: utf-8 -*-
"""Sample model module."""

from sqlalchemy import Column
from sqlalchemy.types import Integer, Unicode

from depot.fields.sqlalchemy import UploadedFileField

from depotexample.model import DeclarativeBase, metadata, DBSession


class UploadedImage(DeclarativeBase):
    __tablename__ = 'uploaded_image'

    uid = Column(Integer, primary_key=True)
    title = Column(Unicode(255), nullable=False)
    file = Column(UploadedFileField())