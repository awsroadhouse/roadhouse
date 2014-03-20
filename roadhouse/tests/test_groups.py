import os
import random
import unittest
import boto
from moto import mock_ec2
import mock
from roadhouse import group
import yaml

from roadhouse import parser
# needs to include ports, TCP/UDP, and

class MockVPC(object):
    id = "vpc-%s" % random.randint(1000, 9999)

class BaseConfigTestCase(unittest.TestCase):
    @mock_ec2
    def setUp(self):
        self.ec2 = boto.connect_ec2('somekey', 'somesecret')

    @property
    def config(self):
        sample = os.path.dirname(__file__) + "/sample.yaml"
        return group.SecurityGroupsConfig.load(sample).configure(self.ec2)

def cc(tmp, ec2):
    # shorthand to create a config and apply
    config = group.SecurityGroupsConfig(tmp).configure(ec2)
    return config.apply(MockVPC())


class CreationTest(BaseConfigTestCase):
    # ensures new groups are created

    @mock_ec2
    def test_creation_no_existing_groups(self):
        # asserts we create a bunch of groups and update none
        c = self.config
        vpc = MockVPC()
        c.apply(vpc)
        self.assertEqual(c.updated_group_count, 0)
        self.assertGreater(c.new_group_count, 0)
        c.apply(vpc)

    @mock_ec2
    def test_no_description(self):
        tmp = {"test_no_description":
                   {"options": {} }}
        config = group.SecurityGroupsConfig(tmp).configure(self.ec2)
        config.apply(MockVPC())
        self.assertGreater(config.new_group_count, 0)


class RemoveExistingRulesTest(unittest.TestCase):

    def setUp2(self):
        # super(RemoveExistingRulesTest, self).setUp()
        self.ec2 = boto.connect_ec2('somekey', 'somesecret')
        self.sg = self.ec2.create_security_group("test_group", "jon is amazing")
        self.sg2 = self.ec2.create_security_group("test_group2", "jon is terrible")
        self.sg.authorize("tcp", 22, 22, "192.168.1.1/32")
        self.sg.authorize("tcp", 100, 110, src_group=self.sg2)
        self.c = group.SecurityGroupsConfig(None)
        self.c.configure(self.ec2)
        self.c.reload_remote_groups()

    @mock_ec2
    def test_remove_duplicate(self):
        self.setUp2()
        rule = parser.Rule.parse("tcp port 22 192.168.1.1") # should get filtered
        result = self.c.filter_existing_rules(rule, self.sg)
        assert len(result) == 0

    @mock_ec2
    def test_make_sure_wrong_group_isnt_removed(self):
        self.setUp2()
        self.sg2 = self.ec2.create_security_group("test_group3", "jon is not bad")
        self.c.reload_remote_groups()
        rule = parser.Rule.parse("tcp port 100-110 test_group3")
        result = self.c.filter_existing_rules(rule, self.sg)
        assert len(result) == 1

    @mock_ec2
    def test_leave_different_ip(self):
        # should not filtered
        self.setUp2()
        rule = parser.Rule.parse("tcp port 22 192.168.1.2")
        result = self.c.filter_existing_rules(rule, self.sg)
        assert len(result) == 1

    @mock_ec2
    def test_leave_different_protocol(self):
        # should not get filtered
        self.setUp2()
        rule = parser.Rule.parse("udp port 22 192.168.1.1")
        result = self.c.filter_existing_rules(rule, self.sg)
        assert len(result) == 1






