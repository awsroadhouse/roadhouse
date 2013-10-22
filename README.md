roadhouse
=========

Library for sanely managing AWS security settings

Why does this exist?

Managing your AWS security settings through the AWS console is problematic for several reasons.  Aside from using the console, your options are to use a library like boto.  This is fine, but really more work than I care to do for my environments.

Roadhouse is an attempt to apply configuration management to AWS's settings.  Think of it as Puppet/Chef/Salt for AWS.



Development
=============

In a virtualenv, `pip install -r requirements`
