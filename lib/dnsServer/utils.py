#This was not written by sonicrules1234, look in namecoindnsserver.py at the top for the actual author
import struct

def label2str(label):
    s = struct.pack("!B", len(label))
    s += label
    return s
    
def labels2str(labels):
    s = ''
    for label in labels:
        s += label2str(label)
    s += struct.pack("!B", 0)
    return s

def ipstr2int(ipstr):
    ip = 0
    i = 24
    for octet in ipstr.split("."):
        ip |= (int(octet) << i)
        i -= 8
    return ip

