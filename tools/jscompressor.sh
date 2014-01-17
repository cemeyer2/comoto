#!/bin/bash
# comoto javascript compressor script

#a few constants
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
COMPRESS="java -jar $DIR/yuicompressor-2.4.2/build/yuicompressor-2.4.2.jar "

#build the compressor
echo "Building Compressor"
cd $DIR
cd yuicompressor-2.4.2
ant build.jar &> /dev/null

#go back to project root
cd $DIR
cd ..
cd MossWeb/mossweb/public/

echo "Starting compression of static JavaScript files"
echo "Deleting old compressed JavaScript files"
find . -name "*min*js" | grep -v yui | xargs rm -f 
echo "Compressing JavaScript files"
for FILE in `find . -name "*.js" | grep -v yui`
do 
echo "Compressing $FILE to $FILE.min.js"
$COMPRESS $FILE -o $FILE.min.js
done

#now dynamic js compression
cd $DIR
cd ..
cd MossWeb/mossweb/templates/js
echo "Starting compression of dynamic JavaScript files"
echo "Deleting old compressed JavaScript files"
find . -name "*min*js" | xargs rm -f 
echo "Compressing JavaScript files"
for FILE in `find . -name "*js"`
do 
echo "Compressing $FILE to $FILE.min.js"
$COMPRESS $FILE -o $FILE.min.js
done

echo "Compression done"

#clean up the compressor
echo "Cleaning up compressor"
cd $DIR
cd yuicompressor-2.4.2
ant clean &> /dev/null
