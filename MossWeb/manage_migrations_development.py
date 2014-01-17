#!/usr/bin/env python
from migrate.versioning.shell import main
main(url='sqlite:///development.db', debug='False', repository='migrations_repository')
