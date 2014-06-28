from __future__ import absolute_import
import os
import ming
from ming import Session
from ming.odm import ThreadLocalODMSession
from ming import create_datastore
from depot.fields.ming import DepotExtension

mainsession = Session()
DBSession = ThreadLocalODMSession(mainsession, extensions=(DepotExtension, ))

database_setup=False
datastore = None


def setup_database():
    global datastore, database_setup
    if not database_setup:
        datastore = create_datastore(os.environ.get('MONGOURL', 'mim:///'))
        mainsession.bind = datastore
        ming.odm.Mapper.compile_all()


def clear_database():
    global datastore, database_setup
    if not database_setup:
        setup_database()

    try:
        # On MIM drop all data
        datastore.conn.drop_all()
    except TypeError:
        # On MongoDB drop database
        datastore.conn.drop_database(datastore.db)

