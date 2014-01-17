#!/bin/sh -x

ARGS="--svnroot https://csil-projects.cs.uiuc.edu/svn/sp10/cs225/ --mp mp4 --file stack.cpp --file queue.cpp --file solidColorPicker.cpp --file solidColorPicker.h --file gradientColorPicker.cpp --file gradientColorPicker.h --file fills.h --file fills.cpp --roster roster-sp10 --solution cmooney2/mp4/"

./sigh.py ${ARGS} --stage fetch && ./sigh.py ${ARGS} --stage moss && ./sigh.py ${ARGS} --stage analyze

