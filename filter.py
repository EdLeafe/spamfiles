#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
from subprocess import Popen, PIPE
import tempfile
import re
import time
import smtplib
import email


MAILHOST = "localhost"
bans = []


def runproc(cmd):
    proc = Popen([cmd], shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE, close_fds=True)
    stdout_text, stderr_text = proc.communicate()
    return stdout_text, stderr_text


class OutputHandler(object):
    def __enter__(self):
        self.out = []
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._close()

    def write(self, *args):
        txt = " ".join(["%s" % arg for arg in args])
        self.out.append(txt)

    def _close(self):
        with open("/var/dummylogs/filter.log", "a", 0) as ff:
            txt = "\n".join(self.out)
            ff.write("%s\n\n" % txt)


def isBannedFromTech(txt):
    for nm in bans:
        if re.search(r"^From.+%s" % nm, txt, re.I | re.M):
            return nm


def isThisOT(txt):
    pat = re.compile(r"^Subject:.*\b[0o]t\b.*", re.I | re.M)
    ret = (pat.search(txt) is not None)

    # Encoded OT
    if not ret:
        pat1252 = re.compile(r"^Subject:.*=\?windows-1252\?Q\?=5BOT=5D.*", re.I | re.M)
        ret = (pat1252.search(txt) is not None)
        
    # World Cup extra
    if not ret:
        #patWC = re.compile("^subject:.*([\[\(\{ ] *wc *[ \]\}\)]).*", re.I | re.M)
        patWC = re.compile(r"^Subject:.*\bwc\b.*", re.I | re.M)
        ret = (patWC.search(txt) is not None)

    return ret


def processPFT(msg, eml):
    OTlog = "/var/dummylogs/techForward.log"
    bannedName = isBannedFromTech(msg)
    if bannedName:
        with open(OTlog, "a") as ff:
            ff.write("Message from %s BANNED from tech; subject: %s\n" % (bannedName, eml["Subject"]))
        return None

    isOT = isThisOT(msg)
    try:
        badHeaders = ["Return-Path", "Reply-To", "Sender", "Errors-To"] + \
                [hd for hd in eml.keys() if hd.startswith("List-")]
        for key in badHeaders:
            try:
                del eml[key]
            except KeyError:
                pass
        try:
            eml.replace_header("To", "profoxtech@leafe.com")
        except KeyError:
            eml.add_header("To", "profoxtech@leafe.com")
        if isOT:
            eml.replace_header("From", "discardme@leafe.com")
        else:
            if eml["Subject"] is None and len(eml.as_string()) < 100:
                eml.add_header("X-EMPTY-MESSAGE", "True")
            else:
                eml.add_header("X-Forwarded-By", "OT filtering script")
            
        ret = eml.as_string()
        outlen = len(ret)
        
        try:
            if isOT:
                logtext = "   <<OT>> Subject: %s  - NOT FORWARDED  (len=%s)\n"
            else:
                logtext = "Subject: %s  Length: %s\n"
            with open(OTlog, "a") as ff:
                ff.write(logtext % (eml["Subject"], outlen))
        except StandardError as e:
            server = smtplib.SMTP(MAILHOST)
            server.sendmail("NonOT@leafe.com", "ed@leafe.com",
                    "To: Ed Leafe <ed@leafe.com>\nSubject: NonOT problem\n\nError encountered: %s" % str(e) )
            server.quit()
        if isOT:
            return None
        else:
            return ret

    except StandardError as e:
        try:
            with open('/usr/local/mailman/badForward.error', 'a') as ff:
                ff.write("\n\n\n%s\n------\n%s\n%s" % (time.localtime(), e, msg))
        except Exception:
            server = smtplib.SMTP(MAILHOST)
            server.sendmail("NonOT@leafe.com", "ed@leafe.com", 
                    "To: Ed Leafe <ed@leafe.com>\nSubject: Bad Forward problem\n\nError encountered: %s" % str(e) )
            server.quit()
        return None
        

def getMsg():
    retVal = ""
    while True:
        ch = sys.stdin.read(1024)
        retVal = retVal + ch
        if not ch:
            break
    return retVal



if __name__ == "__main__":
    process = None
    try:
        listname = sys.argv[2]
        process = sys.argv[1]
    except IndexError:
        try:
            listname = sys.argv[1]
        except IndexError:
            sys.exit(1)

    with OutputHandler() as logger:
        msgText = getMsg()

        with open("/var/dummylogs/raw_messages.txt", "a") as tt:
            tt.write(msgText)
            tt.write("\n\n")
            tt.write("-=" * 40)
            tt.write("\n\n\n")

        eml = email.message_from_string(msgText)
        subj = eml.get("Subject", "")
        tm = time.strftime("%Y-%m-%d %I:%M:%S %p")
        logger.write("%s - %s: \n\tSubject: %s\n\tFrom: %s" % (tm, listname,
                subj, eml.get("From", "")))

        fd, tmpname = tempfile.mkstemp(dir="/home/ed/spam/tmpfiles/")
        os.close(fd)
        with open(tmpname, "w") as ftmp:
            ftmp.write(msgText)

        # Run the actual command
        cmd = "cat %s | sb_filter.py  -d /var/spambayes/hammiedb" % tmpname
        #logger.write("CMD: %s" % cmd)

        out, err = runproc(cmd)
        eml = email.message_from_string(out)

        badPhrases = [r"^From: .*teapartyinfo.org", r"X-Spambayes-Classification: spam",
                r"X-SpamContent-Violation:", r"X-Spambayes-Classification: unsure; 0.8",
                r"X-Spambayes-Classification: unsure; 0.9"]
        for bp in badPhrases:
            mtch = re.search(bp, out, re.I | re.M)
            if mtch:
                if "teaparty" in bp:
                    # Don't add to the spam list; just delete it
                    badmsg = "*** Deleted TeaParty Crap ***"
                else:
                    # Spam; copy it to the spam file
                    with open("/home/ed/spam/listspammail", "a") as ff:
                        ff.write("%s\n" % out)
                    badmsg = "***Removed as SPAM"
                
                # Record the from address and subject
                logger.write("\t%s" % badmsg)
                os.remove(tmpname)
                sys.exit()

        # Clamfilter
        #cmd = "cat %s | clamfilter.py" % tmpname
        #proc = Popen([cmd], shell=True, stdin=PIPE, stdout=PIPE, close_fds=True)
        #qo, qi = (proc.stdout, proc.stdin)
        #out = qo.read()
        if "X-Virus-Found: yes" in out:
            # Spam; copy it to the spam file
            with open("/var/mail/virusmail", "a") as ff:
                ff.write(out)
            logger.write("\t***Removed as VIRUS")
            os.remove(tmpname)
            sys.exit()

        if listname == "profoxtech":
            # Check for OT
            out = processPFT(out, eml)
            if out is None:
                # Not a valid Tech message
                logger.write("\t--> Removed as OT")
                sys.exit(0)

        with open(tmpname, "w") as ftmp:
            ftmp.write(out)
        #logger.write("--wrote tmp file; size=%s--" % len(out))

        # Forward it on
        if process is not None:
            # list command
            cmd = "cat %(tmpname)s |/usr/local/mailman/mail/mailman %(process)s %(listname)s"
        elif listname == "mailman":
            cmd = "cat %(tmpname)s |/var/lib/mailman/mail/mailman post mailman"
        elif listname == "profoxtech":
            cmd = "cat %(tmpname)s | python /usr/local/mailman/bounceDirect.py | " + \
                    "/usr/local/mailman/stripmime.pl "
        elif listname == "dabo-users":
            cmd = "cat %(tmpname)s  | " + \
                    "/usr/local/mailman/stripmime.pl"
        else:
            cmd = "cat %(tmpname)s  | " + \
                    "/usr/local/mailman/stripmime.pl|  " + \
                    "python /usr/local/mailman/stripQuote.py "
        cmd = cmd % locals()
        logger.write("CMD: %s" % cmd)

        outtxt, errtxt = runproc(cmd)
        logger.write("re-writing to tmpfile: %s" % len(outtxt))
        fd, tmpname_out = tempfile.mkstemp(dir="/home/ed/spam/tmpfiles/")
        os.close(fd)
        try:
            logger.write("writing output to %s" % tmpname_out)
            with open(tmpname_out, "w") as ff:
                ff.write(outtxt)
            logger.write("TMPFILE_out write OK")
        except StandardError as e:
            logger.write("WRITE ERR: %s" % e)
            sys.exit()
        logger.write("GONNA POST: %s" % len(outtxt))

        cmd = "cat %(tmpname_out)s | /usr/local/mailman/mail/mailman post %(listname)s" % locals()
        try:
            out, err = runproc(cmd)
            #logger.write("POST RESULT: %s" % qo.read())
        except StandardError as e:
            logger.write("ERROR: %s, %s" % (type(e), e))
