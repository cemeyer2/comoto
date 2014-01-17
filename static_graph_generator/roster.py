#!/usr/bin/env python

# copyright 2008 Alex Lambert <alex@alexlambert.com>
# modified 2010 Charlie Meyer <cemeyer2@illinois.edu>

import sys, random, copy, os, subprocess, re, cgi, pickle
import pysvn, optparse

def main():
        parser = optparse.OptionParser()
        parser.add_option('--svnroot',
                          dest='svnroot',
                          metavar='URL',
                          help='sets the Subversion repository location')

        (options, args) = parser.parse_args()

        if not options.svnroot:
                parser.error('Subversion root URL not specified')

        fetch(options.svnroot)

def fetch(svnRoot):
        client = pysvn.Client()

        pathsListing = [result[0].repos_path.replace('/', '')
                        for result in client.list(svnRoot, recurse=False)]
        netids = filter(lambda x: not x.startswith('_') and len(x) > 0,
                        pathsListing)

        for netid in netids:
		print netid

if __name__ == "__main__":
	main()
