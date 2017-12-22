import os
import sys

from configobj import ConfigObj
from validate import Validator

def read_config():
    basepath = os.path.dirname(os.path.abspath(__file__))
    configfile = os.path.join(basepath, 'crawler.cfg')
    configspec = os.path.join(basepath, 'configspec.cfg')

    if not os.path.isfile(configfile):
        print("Config file does not exist. See README.md")
        sys.exit(1)

    config = ConfigObj(configfile, configspec=configspec)

    validator = Validator()
    result = config.validate(validator)
    
    if result != True:
        print('Config file validation failed!')
        sys.exit(1)

    return config

config = read_config()
