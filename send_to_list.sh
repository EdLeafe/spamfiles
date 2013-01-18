#!/bin/sh
sudo su -l nobody sh -c "cat /home/ed/spam/ham.mbox | /usr/local/mailman/mail/mailman post $1"
