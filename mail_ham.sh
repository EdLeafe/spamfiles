#!/bin/bash

target='ed'

if [ $1 ]
	then target=$1
fi
echo $target

cd /home/$target
sudo mb2md.pl -s /home/ed/spam/ham.mbox -d /home/$target/Maildir
