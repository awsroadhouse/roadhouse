from distutils.core import setup

setup(
    name='roadhouse',
    version='0.6',
    packages=['roadhouse'],
    install_requires=["boto", "pyparsing", "PyYAML"],
    classifiers=["Development Status :: 4 - Beta",
                 "Topic :: Security",
                 "Intended Audience :: Information Technology",
                 "Intended Audience :: System Administrators",
                 "License :: OSI Approved :: BSD License",
                 "Operating System :: POSIX :: Linux",
                 "Operating System :: MacOS :: MacOS X"
                 ],

    url='https://github.com/awsroadhouse/roadhouse',
    license='BSD 2 Clause',
    author='Jon Haddad',
    author_email='jon@jonhaddad.com',
    description='AWS Configuration Mangement',
    keywords="aws, yaml, configuration"
)
