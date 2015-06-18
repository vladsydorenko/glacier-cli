#!/bin/bash

#Install boto if it isn't already installed
if [ ! -d "/usr/local/lib/python2.7/dist-packages/boto" ]; then
    git clone git://github.com/boto/boto.git
	cd boto
	yes | python setup.py install
	cd ..
	rm -rf boto
fi

#Add script to crontab
#write out current crontab
crontab -l > mycron
#get path to current folder
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
#echo new cron into cron file
echo "@weekly $DIR/sync-glacier.py -b >> backup.log" >> mycron
#install new cron file
crontab mycron
rm mycron

#Create vault and start syncronization for first time
python sync-glacier.py -c

rm setup_backup.sh