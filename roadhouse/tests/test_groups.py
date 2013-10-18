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

def cc(tmp, ec2):
    # shorthand to create a config and apply
    config = groups.SecurityGroupsConfig(tmp).configure(ec2)
    return config.apply()


class CreationTest(BaseConfigTestCase):
    # ensures new groups are created

    @mock_ec2
    def test_creation_no_existing_groups(self):
        c = self.config
        c.apply()
        self.assertEqual(c.updated_group_count, 0)
        self.assertGreater(c.new_group_count, 0)

    @mock_ec2
    def test_no_description(self):
        tmp = {"test_no_description":
                   {"options": {} }}
        config = groups.SecurityGroupsConfig(tmp).configure(self.ec2)
        config.apply()
        self.assertGreater(config.new_group_count, 0)

    @mock_ec2
    def test_vpc(self):
        tmp = {"test_vpc":
                   {"options": {"vpc":"test_vpc"} }}

        c = cc(tmp, self.ec2)
        self.assertGreater(c.new_group_count, 0)



class RulesParsingTest(unittest.TestCase):
    def test_tcp_with_ip(self):
        result = groups.Rule.parse("tcp port 80 192.168.1.1/32")
        assert len(result) == 1
        result = result[0]
        assert result.ip == '192.168.1.1'
        assert result.mask == '32'


