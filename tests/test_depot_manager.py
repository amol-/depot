# -*- coding: utf-8 -*-
import unittest
from depot.manager import DepotManager


class TestDepotManager(unittest.TestCase):
    def setUp(self):
        DepotManager._clear()

    def test_first_configured_is_default(self):
        DepotManager.configure('first', {'depot.storage_path': './lfs'})
        DepotManager.configure('second', {'depot.storage_path': './lfs2'})
        assert DepotManager.get_default() == 'first'

    def test_changing_default_depot_works(self):
        DepotManager.configure('first', {'depot.storage_path': './lfs'})
        DepotManager.configure('second', {'depot.storage_path': './lfs2'})
        DepotManager.set_default('second')
        assert DepotManager.get_default() == 'second'

    def test_no_configured_is_detected(self):
        with self.assertRaises(RuntimeError):
            DepotManager.get_default()

    def test_prevent_non_existing_default(self):
        with self.assertRaises(RuntimeError):
            DepotManager.set_default('does_not_exists')

    def test_prevent_multiple_middlewares(self):
        with self.assertRaises(RuntimeError):
            DepotManager.make_middleware(None)
            DepotManager.make_middleware(None)

    def test_detects_no_middleware(self):
        with self.assertRaises(RuntimeError):
            DepotManager.get_middleware()

    def test_prevent_configuring_two_storages_with_same_name(self):
        DepotManager.configure('first', {'depot.storage_path': './lfs'})

        with self.assertRaises(RuntimeError):
            DepotManager.configure('first', {'depot.storage_path': './lfs2'})

    def test_aliases(self):
        DepotManager.configure('first', {'depot.storage_path': './lfs'})
        DepotManager.configure('second', {'depot.storage_path': './lfs2'})

        DepotManager.alias('used_storage', 'first')
        storage = DepotManager.get('used_storage')
        assert storage.storage_path == './lfs', storage

        DepotManager.alias('used_storage', 'second')
        storage = DepotManager.get('used_storage')
        assert storage.storage_path == './lfs2', storage

    def test_aliases_not_existing(self):
        with self.assertRaises(ValueError):
            DepotManager.alias('used_storage', 'first')

    def test_alias_on_existing_storage(self):
        DepotManager.configure('mystorage', {'depot.storage_path': './lfs2'})
    
        with self.assertRaises(ValueError):
            DepotManager.alias('mystorage', 'mystorage')

