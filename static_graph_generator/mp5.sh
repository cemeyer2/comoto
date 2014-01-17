#!/bin/sh -x

ARGS="--svnroot https://csil-projects.cs.uiuc.edu/svn/sp10/cs225/ --mp mp5 --file quadtree.cpp --file quadtree.h --roster roster-sp10 --solution _course/_private/trunk/mp/Quadtrees/solution/"

./sigh.py ${ARGS} --stage fetch && ./sigh.py ${ARGS} --stage moss && ./sigh.py ${ARGS} --stage analyze

