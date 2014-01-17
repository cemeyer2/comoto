#!/bin/sh -x

ARGS="--svnroot https://subversion.ews.illinois.edu/svn/fa10-cs225 --mp mp2 --file image.cpp --file image.h --file scene.cpp --file scene.h --roster netids-cs225-fa10 --solution _class/_private/trunk/mp/ImageManipulation2/solution/"

./sigh.py ${ARGS} --stage fetch && ./sigh.py ${ARGS} --stage moss && ./sigh.py ${ARGS} --stage analyze

