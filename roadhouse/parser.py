from pyparsing import Word, nums, CaselessKeyword, Optional, Combine, And, Keyword, delimitedList, Or, Group, Regex


port_ = CaselessKeyword("port")
tcp_ = CaselessKeyword("tcp")
udp_ = CaselessKeyword("udp")
icmp_ = CaselessKeyword("icmp")

protocol = tcp_ ^ udp_ ^ icmp_

def to_int(s,l,t):
    return [int(t[0])]

def to_port_range(s, l, t):
    if t[0].port or t[0].port==0: # handle ICMP type 0
        return [(t[0].port, t[0].port)]
    else:
        return [(t[0][0].port, t[0][1].port)]

def normalize_ip(t):
    # returns a normalized ip
    return t.ip + "/" + (str(t.mask.mask) if t.mask else "32")


port = Group(Word(nums).setParseAction(to_int)('port'))
port_range = Group((port + Word("-").suppress() + port)('range'))

normalized_port_range = (port ^ port_range).setParseAction(to_port_range)

ports = delimitedList(normalized_port_range)('ports')

# IP addresses, name of another group, or sg-*
security_group = Regex("sg-[\w\d]+")
group_name = Regex("[\w\d\(-|.|_)]+")

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

