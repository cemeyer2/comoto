#!/bin/sh -x

# ugly because we only support checking against one solution at a time right now

BASEARGS="--svnroot https://csil-projects.cs.uiuc.edu/svn/fa09/cs225/ --mp mp7 --file dsets.cpp --file dsets.h --file maze.cpp --file maze.h --roster roster-fa09 --solution"
ARGS1="${BASEARGS} _course/_private/trunk/mp/Mazes/src/"
ARGS2="${BASEARGS} _course/_private/trunk/mp/Mazes/_oldSolution1/"
ARGS3="${BASEARGS} _course/_private/trunk/mp/Mazes/_oldSolution2/"

./sigh.py ${ARGS1} --stage fetch && ./sigh.py ${ARGS1} --stage moss && ./sigh.py ${ARGS1} --stage analyze && mv mp7 mp7-soln1
./sigh.py ${ARGS2} --stage fetch && ./sigh.py ${ARGS2} --stage moss && ./sigh.py ${ARGS2} --stage analyze && mv mp7 mp7-soln2
./sigh.py ${ARGS3} --stage fetch && ./sigh.py ${ARGS3} --stage moss && ./sigh.py ${ARGS3} --stage analyze && mv mp7 mp7-soln3

