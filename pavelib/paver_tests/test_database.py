"""
Tests for the Paver commands for updating test databases
"""
from unittest import TestCase
import os

d = [name for name in sys.modules if name.startswith("six.moves.")]
for name in d:
    del sys.modules[name]
from boto import connect_s3, s3
from mock import patch
from moto import mock_s3

from common.test.utils import MockS3Mixin
from pavelib.database import verify_fingerprint_in_bucket

class TestPaverDatabaseTasks(MockS3Mixin, TestCase):
    """ Tests for the code that does DB manipulation for tests."""
    def setUp(self):
        super(TestPaverDatabaseTasks, self).setUp()
        connection = connect_s3()
        connection.create_bucket('moto_test_bucket')
        self.bucket = connection.get_bucket('moto_test_bucket')


    # @mock_s3
    @patch.dict(os.environ, {'DB_CACHE_S3_BUCKET': 'moto_test_bucket'})
    def test_fingerprint_in_bucket(self):
        from pdb import set_trace; set_trace()
        key = self.bucket.new_key(key_name='testfile.zip')
        # key = boto.s3.key.Key(bucket=self.bucket, name='testfile.zip')
        key.set_contents_from_string('this is a test')
        self.assertTrue(verify_fingerprint_in_bucket('testfile'))


    # @mock_s3
    # @patch.dict(os.environ, {'DB_CACHE_S3_BUCKET': 'moto_test_bucket'})
    # def test_fingerprint_not_in_bucket(self):
    #     key = boto.s3.key.Key(bucket=self.bucket, name='testfile.zip')
    #     key.set_contents_from_string('this is a test')
    #     self.assertFalse(verify_fingerprint_in_bucket('otherfile'))
