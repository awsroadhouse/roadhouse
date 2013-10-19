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



parse = groups.Rule.parse

class RulesParsingTest(unittest.TestCase):
    def test_tcp_with_ip(self):
        result = parse("tcp port 80 192.168.1.1/32")
        assert len(result) == 1
        result = result[0]
        assert result.ip == '192.168.1.1'
        self.assertEqual(result.mask, 32)

    def test_no_tcp_specified(self):
        tmp = parse("port 80 192.168.1.1")[0]
        self.assertEqual("192.168.1.1", tmp.ip)
        self.assertEqual(80, tmp.port)

    def test_ip_range(self):
        tmp = parse("tcp port 80-100 192.168.1.1")[0]
        self.assertEqual(tmp.port_range[0], 80)

        tmp = parse("tcp port 80-100, 100-200 192.168.1.1")[0]
        self.assertEqual(tmp.port_range[0], 80)

    def test_mask(self):

        result = groups.mask.parseString("/32")
        self.assertEqual(result.mask, 32)

class SimplePortParseTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parse = groups.normalized_port_range.parseString

    def test_single_port(self):
        tmp = self.parse("80")
        self.assertEqual(tmp[0], (80, 80))

    def test_port_range(self):
        tmp = self.parse("80-100")
        self.assertEqual(tmp[0], (80, 100))


class PortParseTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parse = groups.ports.parseString

    def test_port_and_range(self):
        tmp = self.parse("22, 80-100")
        self.assertEqual(tmp.ports[0], (22, 22))
        self.assertEqual(tmp.ports[1], (80, 100))

    def test_double_range(self):
        tmp = self.parse("10-20, 80-100")
        self.assertEqual(tmp.ports[0], (10, 20))
        self.assertEqual(tmp.ports[1], (80, 100))





