# convenience method
import yaml
import boto
from boto.ec2 import EC2Connection
import itertools

from parser import  Rule

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

    def vpc_groups(self, vpc):
        return [x for x in self.existing_groups if x.vpc_id == vpc.id]

    @classmethod
    def load(cls, yaml_path):
        tmp = open(yaml_path, 'r').read()
        yaml_as_dict = yaml.load(tmp)
        return SecurityGroupsConfig(yaml_as_dict)

    def reload_remote_groups(self):
        """reloads the existing groups from AWS
        """
        self.existing_groups = self.ec2.get_all_security_groups()

    def apply(self, vpc):
        """
        returns a list of new security groups that will be added
        """
        assert vpc is not None
        # make sure we're up to date
        self.reload_remote_groups()

        vpc_groups = self.vpc_groups(vpc)
        self._apply_groups(vpc)

        # reloads groups from AWS, the authority
        self.reload_remote_groups()
        vpc_groups = self.vpc_groups(vpc)


        groups = {k.name:k for k in vpc_groups}

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
                    group_name = groups.get(rule.group_name, None)
                    if group_name and rule.address:
                        raise Exception("Can't auth an address and a group")

                    logger.debug("Authorizing %s %s %s to address:%s name:%s", rule.protocol,
                                 rule.from_port, rule.to_port, rule.address, rule.group_name)

                    group_to_authorize = groups.get(rule.group_name, None)

                    try:
                        group.authorize(rule.protocol,
                                    rule.from_port,
                                    rule.to_port,
                                    rule.address,
                                    group_to_authorize, None)
                    except Exception as e:
                        print "could not authorize group %s" % group_to_authorize
                        raise

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
                group_match = False
                if rule.group_name:
                    logger.debug("Checking for possible group name match %s", x.grants[0].group_id)

                if rule.group_name and x.grants[0].group_id \
                    and rule.group_name != self.get_group(x.grants[0].group_id).name:
                    logger.debug("Group name %s didn't match %s", rule.group_name, x.grants[0].name)
                    return False

                if x.ip_protocol != rule.protocol:
                    logger.debug("ruled out due to protocol: %s vs %s", x.ip_protocol, rule.protocol)
                    return False

                if int(x.from_port) != int(rule.from_port):
                    logger.debug("ruled out due to from_port: %s vs %s", int(x.from_port), int(rule.from_port))
                    return False

                if int(x.to_port) != (rule.to_port):
                    logger.debug("ruled out due to to_port: %s vs %s", int(x.to_port), int(rule.to_port))
                    return False

                # final checks - if one of these rules matches we already have a matching rule
                # and we return True
                if rule.address and not filter(lambda y: y.cidr_ip == rule.address, x.grants ):
                    logger.debug("%s not found in grants", rule.address)
                    return False

                logger.debug("%s %s ok", rule.address, rule.group_name)
                logger.debug("port_from: %s %s", rule.from_port, x.from_port)
                logger.debug("port_to: %s %s", rule.to_port, x.to_port)
                logger.debug("group: %s %s", rule.group_name, x.to_port)
                return True

            logger.debug("Applying rules for %s", group.name)
            filtered = filter(eq, group.rules)

            if not filtered:
                logger.debug(filtered)
                logger.debug("Applying rule %s against %s", rule, group.rules)
                tmp.append(rule)
        return tmp

    def get_group(self, group_id):
        for x in self.existing_groups:
            if x.id == group_id:
                return x


    def _apply_groups(self, vpc):
        vpc_groups = self.vpc_groups(vpc)

        existing_group_names = [x.name for x in vpc_groups]
        for x,y in self.config.items():
            options = y.get('options', {})
            desc = options.get('description', " ")

            if x not in existing_group_names:
                # create the group
                logger.info("creating group %s", x)
                group = self.ec2.create_security_group(x, desc, vpc_id=vpc.id)
                # set up ports
                self.new_group_count += 1
            else:
                # update desc if it's wrong
                self.updated_group_count += 1




