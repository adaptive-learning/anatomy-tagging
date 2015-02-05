#!/bin/sh
# deployment script run by Viper server after push

echo "Starting deploy script"
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd $DIR


#requirements
python $DIR/setup.py install

# database
python $DIR/manage.py syncdb
python $DIR/manage.py migrate

# static files
python $DIR/manage.py collectstatic --noinput
