# convenience method
import yaml
import boto
from boto.ec2 import EC2Connection

from pyparsing import Word, nums, White, CaselessKeyword

def sync(yaml_file_path, ec2_conn = None):
    # convenience method.  you'll probably always want this for simplicity
    # if ec2_conn is none, we will try to connect using the default settings

    sgc = SecurityGroupsConfig.load(yaml_file_path)
    sgc.configure(ec2_conn)
    sgc.apply_changes()
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

    def apply(self):
        """
        returns a list of new security groups that will be added
        """
        if self.existing_groups is None:
            self.existing_groups = self.ec2.get_all_security_groups()

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
        return self

port = CaselessKeyword("port")


class Rule(object):
    def __init__(self):
        pass

    @classmethod
    def parse(cls, rule_string):
        """
        returns a list of rules
        a single line may yield multiple rules
        """
        result = rule_parser.match(rule_string)
        return [result]
