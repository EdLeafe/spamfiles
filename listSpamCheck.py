#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import time
import smtplib
import re

fname = "/home/ed/Maildir/listspammail"
if not os.path.exists(fname):
	sys.exit()
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
sendPat = re.compile(r"([^<]+)<\S+>")
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
			except:
				subjs[sub] = 1
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
# sublist = "".join(subkeys)
sublist = "\n".join(subnums)
fromkeys = senders.keys()
fromkeys.sort()
fromlist = "\n".join(fromkeys)
numkeys = len(subkeys)

tm = time.strftime("%H:%I %p on %h %d, %Y")

##To Delete: <http://leafe.com/~~delspam?%(justfname)s>
msg = """List Spam Header Check
Time: %(tm)s
Spam File: %(newname)s

Filtered Message Total: %(numkeys)s

Subjects:
==========
%(sublist)s

Filtered Message Total: %(numkeys)s

Senders:
==========
%(fromlist)s


Contents:
==========
%(out)s
""" % locals()
server = smtplib.SMTP("leafe.com")
server.sendmail("listSpamCheck@leafe.com", "ed@leafe.com", 
		"To: Ed Leafe <ed@leafe.com>\nSubject: This is the OLD** List Spam Check\n\n%s" % msg )
server.quit()

