#!/usr/bin/env python

'''
Created on Mar 18, 2010

@author: Charlie Meyer
'''

if __name__ == '__main__':
    from paste.script.serve import ServeCommand
    ServeCommand("serve").run(["--reload", "-v", "development_cemeyer2_local_mysql_innodb.ini"])
