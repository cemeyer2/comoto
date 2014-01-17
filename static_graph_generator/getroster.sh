#!/bin/sh -x

SVN_ROOT="https://subversion.ews.illinois.edu/svn/fa10-cs225/"
OUTPUT_FILE="netids-cs225-fa10"

./roster.py --svnroot $SVN_ROOT | tee $OUTPUT_FILE
