# convenience method
import yaml
import boto
from boto.ec2 import EC2Connection

def sync(yaml_file_path, ec2_conn = None):
    # convenience method.  you'll probably always want this for simplicity
    # if ec2_conn is none, we will try to connect using the default settings

    tmp = open(yaml_file_path, 'r').read()
    yaml_as_dict = yaml.load(tmp)
    return sync_yaml(yaml_as_dict, ec2_conn)

def sync_yaml(y, ec2_conn):
    assert isinstance(y, dict)
    assert isinstance(ec2_conn, EC2Connection)
    # get current groups
    groups = ec2_conn.get_all_security_groups()

    # create new groups
