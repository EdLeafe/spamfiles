#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import time
import smtplib
import re


def main(prfx):
	fname = "/home/ed/spam/%sspammail" % prfx.strip()
	if not os.path.exists(fname):
		return
	fpath, justname = os.path.split(fname)
	
	# Get a unique name for the file
	ext = 0
	while os.path.exists(os.path.join(fpath, "checked", "%s.%s" % (justname, ext))):
		ext += 1
	newname = os.path.join(fpath, "checked", "%s.%s" % (justname, ext))
	justfname = os.path.split(newname)[1]
	
	# Copy the contents
	open(newname, "w").write(open(fname).read())
	# Blank the old
	open(fname, "w")
	os.chmod(newname, 0666)
	
	out = ""
	subjs = {}
	senders = {}
	eds = {}
	sendPat = re.compile(r"([^<]+)<\S+>")
	edPat = re.compile(r"\bED\b")
	f = open(newname)
	for ln in f:
		if ln.startswith("From "):
			out += "\n"
		elif ln.startswith("From: ") or ln.startswith("Subject: "):
			out += ln
			if ln.startswith("Subject: "):
				sub = ln.split(" ", 1)[1]
				try:
					subjs[sub] += 1
				except KeyError:
					subjs[sub] = 1
				if edPat.search(ln):
					try:
						eds[sub] += 1
					except KeyError:
						eds[sub] = 1

			else:
				# Extract the quoted name if possible
				nm = ln.lstrip("From: ")
				mtch = sendPat.match(nm)
				if mtch:
					key = mtch.groups()[0].strip()
				else:
					key = nm
				senders[key] = 1
	f.close()
	
	subkeys = [(999-v, k) for k,v in subjs.items()]
	subkeys.sort()
	subnumsTmp = ["[%s] %s" % (subjs[kk], kk.strip()) for vv,kk in subkeys]
	subnums = [ss.replace("[1] ", "") for ss in subnumsTmp]
	sublist = "\n".join(subnums)
	fromkeys = senders.keys()
	fromkeys.sort()
	fromlist = "\n".join(fromkeys)
	numkeys = len(subkeys)

	edkeys = [(999-v, k) for k,v in eds.items()]
	edkeys.sort()
	ednumsTmp = ["[%s] %s" % (eds[kk], kk.strip()) for vv,kk in edkeys]
	ednums = [ss.replace("[1] ", "") for ss in ednumsTmp]
	edlist = "\n".join(ednums)
	
	tm = time.strftime("%H:%I %p on %h %d, %Y")
	msgHeader = "%sSpam Header Check" % prfx.title()
	
	msg = """%(msgHeader)s
Time: %(tm)s
Spam File: %(newname)s

Filtered Message Total: %(numkeys)s
To Delete: <http://mail.leafe.com/cgi-bin/delspam/%(justfname)s>

Subjects:
==========
%(sublist)s

Filtered Message Total: %(numkeys)s
To Delete: <http://mail.leafe.com/cgi-bin/delspam/%(justfname)s>

ED Subjects:
============
%(edlist)s

Senders:
==========
%(fromlist)s

To Delete: <http://mail.leafe.com/cgi-bin/delspam/%(justfname)s>

Contents:
==========
%(out)s

To Delete: <http://mail.leafe.com/cgi-bin/delspam/%(justfname)s>
""" % locals()
	server = smtplib.SMTP("mail.leafe.com")
	if prfx:
		recip = "%sSpamCheck@leafe.com" % prfx.strip()
	else:	
		recip = "spamCheck@leafe.com"
	msgSubj = "%sSpam Check" % prfx.title()
	server.sendmail(recip, "ed@leafe.com", 
			"To: Ed Leafe <ed@leafe.com>\nSubject: %s\n\n%s" % (msgSubj, msg))
	server.quit()

if __name__ == "__main__":
	for listType in ("", "list "):
		main(listType)
