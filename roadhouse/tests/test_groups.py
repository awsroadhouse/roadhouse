import unittest
from moto import mock_ec2



# needs to include ports, TCP/UDP, and
sample1 = """

test_database_group: some useful description
    - tcp port 22-40 192.160.1.1/32
    - tcp port 80 192.168.1.1/32
    - udp port 999 sg-whatever
"""

class SyncTest(unittest.TestCase):
    def test_

class CreationTest(unittest.TestCase):
    # ensures new group is created
    @mock_ec2
    def test_creation(self):
        pass


class RuleUpdateTest(unittest.TestCase):
    pass

