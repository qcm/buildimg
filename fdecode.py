#!/usr/bin/python
import binascii

# arg: txt input file
# ret: returning 0 when successfully write in tlv
def getRSAData(fname):
	output = []
	rsa_str = ''
	rsa_tmp = ''
	exponent = '0xff'
	fin = open(fname, 'r')
	for line in fin:
		if 'M' in line:
			continue
		if 'E' in line:
			ind1 = line.find('(')
			ind2 = line.find(')')
			exponent = line[ind1+1:ind2].strip('0xX').zfill(2)
		else:
			tmp1 = line.strip(' :\n') 
			if len(tmp1) == 0: continue
			tmp2 = tmp1.split(':')
			output += tmp2
	output.pop(0)		
	output.append(exponent)
	for i in output:
		rsa_tmp += i
		rsa_str += binascii.a2b_hex(i)
	print rsa_tmp
	return rsa_str

print getRSAData('rsa.txt')
