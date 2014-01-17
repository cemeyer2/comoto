#!/usr/bin/env python
from migrate.versioning.shell import main
main(url='mysql://nah_this_has_been_sanitized@localhost/comoto2', debug='False', repository='migrations/')
