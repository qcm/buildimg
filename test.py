#!/usr/bin/python
import getopt
import sys
ix = 144
def main():
	global ix
	print 'test'
	opts, args = getopt.getopt(sys.argv[1:], "ha:A:")
    	for o, a in opts:
        	if o in ("-h"):
			print 'help'
		if o == "-a":
			print 'a'
			ix = int(a,16)
			#print ix
		if o == "-A":
			print 'A'
			ix = int(a,16)
	print ix

main()
