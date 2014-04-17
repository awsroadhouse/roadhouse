import unittest
from roadhouse import parser

class PortParseTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parse = parser.ports.parseString

    def test_port_and_range(self):
        tmp = self.parse("22, 80-100")
        self.assertEqual(tmp.ports[0], (22, 22))
        self.assertEqual(tmp.ports[1], (80, 100))

    def test_double_range(self):
        tmp = self.parse("10-20, 80-100")
        self.assertEqual(tmp.ports[0], (10, 20))
        self.assertEqual(tmp.ports[1], (80, 100))

class RuleParseTest(unittest.TestCase):
    def test_single_rule(self):
        result = parser.Rule.parse("tcp port 80 127.0.0.1/32")

        self.assertEqual(len(result), 1)
        tmp = result[0]
        self.assertTrue(isinstance(tmp, parser.Rule))
        self.assertEqual(tmp.from_port, 80)
        self.assertEqual(tmp.to_port, 80)

    def test_group_name_parse(self):
        inputs=["web_server", "web-server", "web.server"]
        for input in inputs:
            result = parser.Rule.parse("tcp port 80 {}".format(input))[0]
            self.assertTrue(isinstance(result, parser.Rule))

    def test_sg_parse(self):
        sg = "sg-edcd9784"
        result = parser.Rule.parse("tcp port 80 {}".format(sg))[0]
        self.assertEqual(result.group, sg)


class RulesParsingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parse = parser.parser.parseString

    def test_tcp_with_ip(self):
        result = self.parse("tcp port 80 192.168.1.1/32")
        self.assertEqual(result.protocol, "tcp")
        self.assertEqual(result.ip_and_mask, "192.168.1.1/32")
        self.assertEqual(result.ports[0], (80, 80))

    def test_multiple_ports(self):
        result = self.parse("tcp port 80, 100 192.168.1.1/32")

        self.assertEqual(result.ports[0], (80,80))
        self.assertEqual(result.ports[1], (100,100))

        # def test_no_tcp_specified(self):
        #     tmp = self.parse("port 80 192.168.1.1")
        #     self.assertEqual("192.168.1.1", tmp.ip)
        #     self.assertEqual(tmp.ports[0], (80,80))


class IPTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.parse = parser.ip.parseString

    def test_ip_no_mask(self):
        # ensurs we get the mask added as /32
        tmp = self.parse("192.168.1.1")[0]
        self.assertEqual("192.168.1.1/32", tmp)

    def test_ip_with_mask(self):
        tmp = self.parse("192.168.1.1/32")[0]
        self.assertEqual("192.168.1.1/32", tmp)


class MaskTest(unittest.TestCase):
    def test_mask(self):
        result = parser.mask.parseString("/32")
        self.assertEqual(result.mask, 32)

class SimplePortParseTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parse = parser.normalized_port_range.parseString

    def test_single_port(self):
        tmp = self.parse("80")
        self.assertEqual(tmp[0], (80, 80))

    def test_port_range(self):
        tmp = self.parse("80-100")
        self.assertEqual(tmp[0], (80, 100))
