#!/bin/sh -x

# ugly because we only support checking against one solution at a time right now

BASEARGS="--svnroot https://csil-projects.cs.uiuc.edu/svn/fa09/cs225/ --mp mp6 --file kdtilemapper.cpp --file kdtilemapper.h --file kdtree.cpp --file kdtree.h --roster roster-fa09 --solution"
ARGS1="${BASEARGS} _course/_private/trunk/mp/PhotoMosaic/src/"
ARGS2="${BASEARGS} _course/_private/trunk/mp/PhotoMosaic_fa08/src/"
ARGS3="${BASEARGS} _course/_private/trunk/mp/PhotoMosaic_sp09/src/"

./sigh.py ${ARGS1} --stage fetch && ./sigh.py ${ARGS1} --stage moss && ./sigh.py ${ARGS1} --stage analyze && mv mp6 mp6-soln1
./sigh.py ${ARGS2} --stage fetch && ./sigh.py ${ARGS2} --stage moss && ./sigh.py ${ARGS2} --stage analyze && mv mp6 mp6-soln2
./sigh.py ${ARGS3} --stage fetch && ./sigh.py ${ARGS3} --stage moss && ./sigh.py ${ARGS3} --stage analyze && mv mp6 mp6-soln3

