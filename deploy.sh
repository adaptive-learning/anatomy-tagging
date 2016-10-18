#!/bin/sh
# deployment script run by Viper server after push

echo "Starting deploy script"
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd $DIR


echo " * setup.py install requirements"
python $DIR/setup.py install

echo " * syncdb and migrate"
python $DIR/manage.py syncdb
python $DIR/manage.py migrate

echo " * collect static | tail"
python $DIR/manage.py collectstatic --noinput | tail

echo " * anatomy data"
python $DIR/manage.py load_images 
python $DIR/manage.py load_terms
python $DIR/manage.py relate_terms
python $DIR/manage.py sanitize_terms --canonical-names

echo "HASH = '$(date +%s)'" > $DIR/githash.py
