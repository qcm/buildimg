#!/usr/bin/python
import binascii

# arg: txt input file
# ret: returning 0 when successfully write in tlv
def getRSAData(fname):
	output = []
	rsa_bin = ''
	rsa = ''
	exponent = '0x00'
	fin = open(fname, 'r')
	for line in fin:
		if 'M' in line:
			continue
		if 'E' in line:
			ind1 = line.find('(')
			ind2 = line.find(')')
			exponent = line[ind1+1:ind2].strip('0xX')
			if len(exponent) == 1:
				exponent = exponent.zfill(2)	
			elif len(exponent) == 3:
				exponent = exponent.zfill(4)	
			elif len(exponent) == 5:
				exponent = exponent.zfill(6)	
			elif len(exponent) == 7:
				exponent = exponent.zfill(8)	
		else:
			tmp1 = line.strip(' :\n') 
			if len(tmp1) == 0: continue
			tmp2 = tmp1.split(':')
			output += tmp2
	output.pop(0)		
	output.append(exponent)
	for i in output:
		rsa += i
		rsa_bin += binascii.a2b_hex(i)
	print rsa
	return rsa_bin

print getRSAData('rsa.txt')
