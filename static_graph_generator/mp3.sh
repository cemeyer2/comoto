#!/bin/sh -x

ARGS="--svnroot https://csil-projects.cs.uiuc.edu/svn/sp10/cs225 --mp mp3 --file mp3extras.cpp --roster roster-sp10 --solution _course/_private/trunk/mp/LinkedLists/solution/"

./sigh.py ${ARGS} --stage fetch && ./sigh.py ${ARGS} --stage moss && ./sigh.py ${ARGS} --stage analyze

