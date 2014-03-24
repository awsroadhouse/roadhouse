roadhouse
=========

Library for sanely managing AWS security settings

Why does this exist?

Managing your AWS security settings through the AWS console is problematic for several reasons.  Aside from using the console, your options are to use a library like boto.  This is fine, but really more work than I care to do for my environments.

Roadhouse is an attempt to apply configuration management to AWS's settings.  Think of it as Puppet/Chef/Salt for AWS.



Development
=============

In a virtualenv, `pip install -r requirements`


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

