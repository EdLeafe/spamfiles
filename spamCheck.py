#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import os
import re
import smtplib
import sys
import time


def process(fname, prfx=""):
    out = ""
    subjs = {}
    senders = {}
    recips = {}
    eds = {}
    sendPat = re.compile(r"([^<]+)<\S+>")
    edPat = re.compile(r"\bED\b")
    with open(fname) as spamfile:
        for ln in spamfile:
            if ln.startswith("From "):
                out += "\n"
            elif ln.startswith("Subject: "):
                out += ln
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
            elif ln.startswith("From: ") or ln.startswith("X-Original-To: "):
                out += ln
                if ln[0] == "F":
                    # Extract the quoted name if possible
                    nm = ln.lstrip("From: ")
                    mtch = sendPat.match(nm)
                    if mtch:
                        key = mtch.groups()[0].strip()
                    else:
                        key = nm
                    senders[key] = 1
                else:
                    nm = ln.lstrip("X-Original-To: ")
                    try:
                        recips[nm] += 1
                    except KeyError:
                        recips[nm] = 1

    itms = subjs.items()
    total = sum([v for k, v in itms])
    subkeys = [(999-v, k) for k,v in itms]
    subkeys.sort()
    subnumsTmp = ["[%s] %s" % (subjs[kk], kk.strip()) for vv,kk in subkeys]
    subnums = [ss.replace("[1] ", "") for ss in subnumsTmp]
    sublist = "\n".join(subnums)
    fromkeys = senders.keys()
    fromkeys.sort()
    fromlist = "\n".join(fromkeys)

    # Remove the most likely subjects
    spamwords = [
            "refinance",
            "obama",
            "testosterone",
            "president",
            "shopping",
            ]

    recipkeys = [(999-v, k) for k,v in recips.items()]
    recipkeys.sort()
    recipnums = ["[%s] %s" % (recips[kk], kk.strip()) for vv,kk in recipkeys]
    reciplist = "\n".join(recipnums)

    edkeys = [(999-v, k) for k,v in eds.items()]
    edkeys.sort()
    ednumsTmp = ["[%s] %s" % (eds[kk], kk.strip()) for vv,kk in edkeys]
    ednums = [ss.replace("[1] ", "") for ss in ednumsTmp]
    edlist = "\n".join(ednums)

    justfname = os.path.split(fname)[1]
    tm = time.strftime("%H:%I %p on %h %d, %Y")
    msgHeader = "%sSpam Header Check" % prfx.title()

    msg = """%(msgHeader)s
Time: %(tm)s
Spam File: %(fname)s

Filtered Message Total: %(total)s
To Delete: <http://mail.leafe.com/cgi-bin/delspam/%(justfname)s>

Subjects:
==========
%(sublist)s

Filtered Message Total: %(total)s
To Delete: <http://mail.leafe.com/cgi-bin/delspam/%(justfname)s>

Recipients:
============
%(reciplist)s

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


def main(prfx):
    fname = "/home/ed/spam/%sspammail" % prfx.strip()
    if not os.path.exists(fname):
        return
    fpath, justname = os.path.split(fname)

    # Get a unique name for the file
    sprfx = prfx.strip()
    nm = sprfx + datetime.datetime.now().strftime("%Y%b%d_%H%M")
    if os.path.exists(os.path.join(fpath, "checked", nm)):
        # Add the seconds if needed
        nm = sprfx + datetime.datetime.now().strftime("%Y%b%d_%H%M%S")
    newname = os.path.join(fpath, "checked", nm)

    # Copy the contents
    with open(newname, "w") as newspam:
        with open(fname) as oldspam:
            newspam.write(oldspam.read())
    # Blank the old
    with open(fname, "w") as oldspam:
        pass
    os.chmod(newname, 0666)

    # Process the file
    process(newname, prfx)


if __name__ == "__main__":
    for listType in ("", "list "):
        main(listType)
