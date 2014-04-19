roadhouse
=========

Library for sanely managing AWS security settings

Why does this exist?

Managing your AWS security settings through the AWS console is problematic for several reasons.  Aside from using the console, your options are to use a library like boto.  This is fine, but really more work than I care to do for my environments.

Roadhouse is an attempt to apply configuration management to AWS's settings.  Think of it as Puppet/Chef/Salt for AWS.

Within roadhouse, a config can be applied to a VPC.  This allows the same configuration to be used across multiple VPCs.  It's useful in cases where you want to run multiple VPCs with the same configuration.  For instance, this is useful when running across multiple datacenters for fault tolerance.

Config File Syntax
====================

The config file is YAML based.  Groups are the top level object.  Within a group are options and rules.  Rules are specified using a syntax similar to tcpdump (at a very, very trivial level).
For ICMP protocol we use ICMP Type Numbers for port. More information is available at: https://www.iana.org/assignments/icmp-parameters/icmp-parameters.xhtml

    - <protocol:optional, tcp by default> <port> <group_or_ip_mask_optional>

It should be easier to understand a valid configuration based on example:

    test_database_group:
      options:
        description: cassandra and redis
        prune: true # remove rules not listed here

      rules:
        - tcp port 22 166.1.1.1/32 # mysterious office IP
        - tcp port 9160, 6379 test_web_group # refer to a group by name
        - port 55 192.168.1.1 # /32 by default
        - tcp port 22-50, 55-60 192.168.1.1
        - icmp port 0 192.168.1.1 # ICMP Type 0; Echo Reply

    test_web_group:
      options:
        description: web servers
        prune: false # false by default

      rules:
        - tcp port 80 0.0.0.0/0
        - icmp port 8 192.168.1.1/32 # ICMP Type 13; Timestamp


Usage
======

    from roadhouse.group import SecurityGroupsConfig
    v = vpc.connect_to_region('us-west-1')
    e = ec2.connect_to_region('us-west-1')

    # assuming you only have 1 vpc already created
    # otherwise you'll need to pick the right VPC you want
    # to apply your changes to
    vpc = v.get_all_vpcs()[0]

    config = SecurityGroupsConfig.load("roadhouse.yaml")
    config.configure(ec2_conn)
    config.apply(vpc)


Development
=============

In a virtualenv, `pip install -r requirements`

