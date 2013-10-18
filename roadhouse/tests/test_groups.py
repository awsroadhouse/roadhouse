import unittest
import boto
from moto import mock_ec2
import mock
from roadhouse import groups
import yaml

# needs to include ports, TCP/UDP, and

class BaseConfigTestCase(unittest.TestCase):
    def setUp(self):
        self.ec2 = boto.connect_ec2('somekey', 'somesecret')

    @property
    def config(self):
        return groups.SecurityGroupsConfig.load('sample.yaml').configure(self.ec2)


class CreationTest(BaseConfigTestCase):
    # ensures new groups are created

    @mock_ec2
    def test_creation_no_existing_groups(self):
        c = self.config
        self.assertGreater(c.new_group_count, 0)
        self.assertEqual(c.updated_group_count, 0)

    @mock_ec2
    def test_no_description(self):
        tmp = {"test_no_description":
                   {"options": {} }}
        config = groups.SecurityGroupsConfig(tmp).configure(self.ec2)
        config.apply()
        self.assertGreater(config.new_group_count, 0)

