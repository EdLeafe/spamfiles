import smtplib, os, re, time

pth = "/usr/local/mailman/data/"
msglst = [ f for f in os.listdir(pth)
		if f.startswith("heldmsg-") ]

if msglst:
	pat = re.compile("heldmsg\-(\S+)\-\d+\.pck")
	heldLists = {}
	for heldMsg in msglst:
		try:
			lst = pat.match(heldMsg).groups()[0]
		except AttributeError:
			print "No Match:", heldMsg
			continue
		if heldLists.has_key(lst):
			heldLists[lst] += 1
		else:
			heldLists[lst] = 1

	hdr = """From: Queue Watch <qw@leafe.com>
X-Mailer: qCheck script
To: Listmom <ed@leafe.com>
Subject: Queue Watch
Date: %s

""" % time.strftime("%c")
	
	msg = ""
	for lst in heldLists.keys():
		msg += "%s: %s held message(s)\n" % (lst, heldLists[lst])
	msg = hdr + msg
	
	oSMTP = smtplib.SMTP("localhost")
	oSMTP.sendmail("qw@leafe.com", "ed@leafe.com", msg)
