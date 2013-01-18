#!/usr/bin/env python
"""Accepts a stream, and scans it for viruses, etc., using clamd."""
import os
import sys
import tempfile
import email


def getMsg():
	ret = ""
	while True:
		txt = sys.stdin.read()
		if txt:
			ret += txt
		else:
			break
	return ret
	

msg = getMsg()
fd, tmpname = tempfile.mkstemp()
os.close(fd)
open(tmpname, "w").write(msg)

sin, sout, serr = os.popen3("cat %s | clamdscan -" % tmpname)
result = sout.read()
res0 = result.splitlines()[0]
res = res0.split("stream: ")[-1].strip()
try:
	os.remove(tmpname)
except: pass

if res == "OK":
	print msg
else:
	eml = email.message_from_string(msg)
	eml.add_header("X-Virus-Found", "yes")
	eml.__setitem__("X-Virus-Status", res)
	print eml.as_string()
