# convenience method
import yaml
import boto
from boto.ec2 import EC2Connection
import itertools

from pyparsing import Word, nums, CaselessKeyword, Optional, Combine, And, Keyword, delimitedList, Or, Group, Regex

import logging

logger = logging.getLogger(__name__)

def sync(yaml_file_path, ec2_conn = None):
    # convenience method.  you'll probably always want this for simplicity
    # if ec2_conn is none, we will try to connect using the default settings

    sgc = SecurityGroupsConfig.load(yaml_file_path)
    sgc.configure(ec2_conn)
    sgc.apply()
    return sgc


class SecurityGroupsConfig(object):

    existing_groups = None

    def __init__(self, config):
        """
        config is a dictionary of configuration options
        """
        self.config = config
        self.new_group_count = 0
        self.updated_group_count = 0

    def configure(self, ec2_conn):
        self.ec2 = ec2_conn
        return self

    @classmethod
    def load(cls, yaml_path):
        tmp = open(yaml_path, 'r').read()
        yaml_as_dict = yaml.load(tmp)
        return SecurityGroupsConfig(yaml_as_dict)

    def reload_remote_groups(self):
        """reloads the existing groups from AWS
        """
        self.existing_groups = self.ec2.get_all_security_groups()

    def apply(self):
        """
        returns a list of new security groups that will be added
        """
        if self.existing_groups is None:
            self.reload_remote_groups()

        self._apply_groups()

        # reloads groups
        self.reload_remote_groups()

        groups = {k.name:k for k in self.existing_groups}

        for x,y in self.config.items():
            # process 1 security group at a time
            group = groups[x]
            if y.get('rules'):
                # apply all rule changes
                rules = [Rule.parse(rule) for rule in y.get('rules')]
                rules = list(itertools.chain(*rules))

                rules = self.filter_existing_rules(rules, group)
                # need to use chain because multiple rules can be created for a single stanza
                for rule in rules:
                    group.authorize(rule.protocol,
                                    rule.from_port,
                                    rule.to_port,
                                    rule.address,
                                    groups.get(rule.group_name, None))
                # apply rules

        return self

    def filter_existing_rules(self, rules, group):
        """returns list of rules with the existing ones filtered out
        :param group security group we need to check the rules against
        :type group boto.ec2.securitygroup.SecurityGroup
        :rtype list of Rule
        """
        tmp = []
        for rule in rules:

            def eq(x):
                # returns True if this existing AWS rule matches the one we want to create
                assert isinstance(x, boto.ec2.securitygroup.IPPermissions)
                # these are simple catches that determine if we can rule out
                # the existing rule
                if x.ip_protocol != rule.protocol:
                    logger.debug("ruled out due to protocol: %s vs %s", x.ip_protocol, rule.protocol)
                    return False

                if x.from_port != rule.from_port:
                    logger.debug("ruled out due to from_port: %s vs %s", x.from_port, rule.from_port)
                    return False

                if x.to_port != rule.to_port:
                    logger.debug("ruled out due to to_port: %s vs %s", x.to_port, rule.to_port)
                    return False

                # final checks - if one of these rules matches we already have a matching rule
                # and we return True
                if rule.address and not filter(lambda y: y.cidr_ip == rule.address, x.grants ):
                    logger.debug("%s not found in grants", rule.address)
                    return False
                # if we fall through to here, none of our tests failed,
                # thus, we match
                if rule.group_name:
                    logger.debug("Checking group name %s against known groups", rule.group_name)

                    if not filter(lambda z: z.name == rule.group_name, x.grants):
                        logger.debug("Group name %s didn't match", rule.group_name)
                        return False


                logger.debug("%s %s ok", rule.address, rule.group_name)
                return True

            if not filter(eq, group.rules):
                tmp.append(rule)
        return tmp



    def _apply_groups(self):
        existing_group_names = [x.name for x in self.existing_groups]

        for x,y in self.config.items():
            options = y.get('options', {})
            desc = options.get('description', " ")

            if x not in existing_group_names:
                # create the group
                group = self.ec2.create_security_group(x, desc)
                # set up ports
                self.new_group_count += 1
            else:
                # update desc if it's wrong
                self.updated_group_count += 1





port_ = CaselessKeyword("port")
tcp_ = CaselessKeyword("tcp")
udp_ = CaselessKeyword("udp")

protocol = tcp_ ^ udp_

def to_int(s,l,t):
    return [int(t[0])]

def to_port_range(s, l, t):
    if t[0].port:
        return [(t[0].port, t[0].port)]
    else:
        return [(t[0][0].port, t[0][1].port)]

def normalize_ip(t):
    # returns a normalized ip
    return t.ip + "/" + (str(t.mask.mask) if t.mask else "32")


port = Group(Word(nums).setParseAction(to_int)('port'))
port_range = Group((port + Word("-").suppress() + port)('range'))

normalized_port_range = (port ^ port_range).setParseAction(to_port_range)

ports  = delimitedList(normalized_port_range)('ports')

# IP addresses, name of another group, or sg-*
security_group = Regex("sg-[\w\d]+")
group_name = Regex("[\w\d\-]+")

mask = Word("/") + Word(nums).setParseAction(to_int)('mask')
ip= (Combine(Word(nums) + ('.' + Word(nums))*3)('ip') + Optional(mask)('mask')).setParseAction(normalize_ip)

parser = Optional(protocol)('protocol') + \
         Optional(port_) + \
         ports + \
         (ip.setResultsName('ip_and_mask') ^ security_group.setResultsName('security_group') ^ group_name('group_name'))


class Rule(object):

    def __init__(self, protocol, from_port, to_port, address=None, group=None, group_name=None):
        """constructs a new rule
        :param protocol tcp or udp
        :param from_port
        :param to_port
        :param address
        :param group sg-style (should almost never be used)
        :param group_name
        """
        self.protocol = protocol or "tcp"
        self.from_port = from_port
        self.to_port = to_port
        self.address = address
        self.group = group
        self.group_name = group_name

    @classmethod
    def parse(cls, rule_string):
        """
        returns a list of rules
        a single line may yield multiple rules
        """
        result = parser.parseString(rule_string)
        rules = []
        # breakout port ranges into multple rules

        kwargs = {}

        kwargs['address'] = result.ip_and_mask or None
        kwargs['group'] = result.security_group or None
        kwargs['group_name'] = result.group_name or None

        for x,y in result.ports:
            r = Rule(result.protocol, x, y, **kwargs)
            rules.append(r)
        return rules

