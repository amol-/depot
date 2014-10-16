# -*- coding: utf-8 -*-
from nose.tools import raises
from depot.manager import DepotManager


class TestDepotManager(object):
    def setup(self):
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

    @raises(RuntimeError)
    def test_no_configured_is_detected(self):
        DepotManager.get_default()

    @raises(RuntimeError)
    def test_prevent_non_existing_default(self):
        DepotManager.set_default('does_not_exists')

    @raises(RuntimeError)
    def test_prevent_multiple_middlewares(self):
        DepotManager.make_middleware(None)
        DepotManager.make_middleware(None)

    @raises(RuntimeError)
    def test_detects_no_middleware(self):
        DepotManager.get_middleware()

    def test_prevent_configuring_two_storages_with_same_name(self):
        DepotManager.configure('first', {'depot.storage_path': './lfs'})

        try:
            DepotManager.configure('first', {'depot.storage_path': './lfs2'})
        except RuntimeError:
            pass
        else:
            assert False, 'Should have raised RunetimeError here'



