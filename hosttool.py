"""Tool for generating host recognize image.

Copyright (c) 2012 by QUALCOMM Atheros, Incorporated.
All Rights Reserved.
QUALCOMM Confidential and Proprietary

Translate from the original C implementation (QCA).

CRC32 algo: crc32 half byte.

"""

import binascii
import struct
import sys
import os
import getopt

__version__ = "1.0.0"

# default global variables
ga_t = ''
ga_i = ''
ga_o = ''
ga_l = 0x0
ga_j = 0x0
g_log = 3
ga_b = 0
ga_p = 0
ga_s = ''
ga_f = ''
# hardcore, fix signature algorithm RSA-2048 SHA256
ga_tlv_sign_algo = 2 
# 0:Ack With VS and CC Event; 1: With CC Event Only; 2: With Status Event Only; 3: NO Ack for each TLV Download Req 
ga_tlvrsp = 0
ga_image_type = 1
ga_tlv_type = 1
ga_tlv_len = 0
ga_crc_ver = 1
ga_patch_ctl = 0x80000000
ga_anti_rollback_version = 0

"""Usage of this tool.
"""
def usage():
	h = """
---------------------------- host_tools usage -----------------------------
    -h:    host_tools usage
    -t:    specify production Types / ID
    -f:    format of the output file, dfu or not
    -l:    the address of the file will be downLoaded to
    -j:    the address of the application's entry
    -O:    operation [patch, table, ramps ...]
    -c:    config file for patch
    -p:    image of patch
    -b:    patchee's rom build version
    -p:    patchee's patch build version
    -a:    patch response/event config 
             0: Ack With VS and CC Event;
             1: Ack With CC Event Only;
             2: Ack With Status Event Only;
             3: NO Ack for each TLV Download Req 
    -i:    input file
    -o:    output file
    -r:    image type
    -s:    image anti-rollback version
---------------------------------------------------------------------------
  Example:
   python %s -t ROME -l 0x1234 -j 0x4567 -i file.bin -o file.dfu
"""
	print h % os.path.basename(__file__)

"""Process command line arguments to rewrite default vaule.
"""
def prerun():
    try:
            opts, args = getopt.getopt(sys.argv[1:], "ht:l:j:i:o:f:c:p:a:r:s:b:O:x:S:R:H:p",
                                   ["help", "type=", "file=", "output="])
    except getopt.GetoptError:
        # print help information and exit:
        usage()
        sys.exit(2)

    if len(sys.argv) < 5:
        print 'Please input more arguments!'
        usage()
        sys.exit(2)
    global ga_t, ga_l, ga_j, ga_i, ga_o, ga_b, ga_p, ga_f, ga_tlvrsp, ga_image_type, ga_anti_rollback_version
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        if o == "-l":
            ga_l = int(a, 16)
        if o == "-j":
            ga_j = int(a, 16)
        if o == "-i":
            ga_i = a
        if o == "-o":
            ga_o = a
        if o == "-t":
            ga_t = int(a, 16)
        if o == "-b":
            ga_b = int(a, 16)
        if o == "-p":
            ga_p = int(a, 16)
        if o == "-f":
            ga_f = a
        if o == "-a":
            ga_tlvrsp = int(a, 8)
        if o == "-x":
            ga_image_type = int(a, 8)
        if o == "-z":
            ga_anti_rollback_version = int(a, 32)

"""PrinT log info by debug level for debug.
"""
def pt(level=3, s=''):
    if level <= g_log:
        print '[LOG%d]%s%s' % (level, (2**(level-1))*' ', s)
           
"""Entrance of this tool.
"""
def main():
    prerun();
    pt(1, '===============================================================')
    pt(1, 'Input file: %s' % ga_i)
    pt(1, 'Output file: %s' % ga_o)
    pt(1, 'Maximal log level: %d' % g_log)
    pt(1, 'Load address: 0x%x' % ga_l)
    pt(1, 'Entry address: 0x%x' % ga_j)
    pt(1, 'Build Ver: 0x%x' % ga_b)
    pt(1, 'Patch Ver: 0x%x' % ga_p)
    pt(1, 'Product ID: 0x%x' % ga_t)
    pt(1, 'Patch Format: %s' % ga_f)
    pt(1, 'Patch Event/Rsp Config: %s' % ga_tlvrsp)
    pt(1, 'Patch Image type: 0x%x' % ga_image_type)
    pt(1, 'Anti-rollback version: 0x%x' % ga_anti_rollback_version)
    pt(1, '===============================================================')

    fin = open(ga_i, 'rb')
    fout = open(ga_o, 'wb')
    fin_cont = fin.read()           
    
    if( ga_f == 'dfu' ):    
        # DFU header struct, Host driver(egret version) compatible
        #   1. load_addr,
        #   2. entry_addr,
        #   3. file_length,
        #   4. crc32
        #   5. dfu type
        #   6. patch content    
        #   7. rom version (32 bit)        
        #   8. build version (32 bit)      
        content = struct.pack("I", ga_l)
        fout.write(content)# 1
        content = struct.pack("I", ga_j)
        fout.write(content)# 2
        ga_s = os.path.getsize(ga_i)
        ga_s = ga_s + 8                     
        content = struct.pack("I", ga_s)   
        fout.write(content)# 3  
        crc32 = (~binascii.crc32(fin_cont)) & 0xFFFFFFFF
        #print '%x' % crc32
        content = struct.pack("I", crc32)
        fout.write(content)# 4
        content = struct.pack("I", 0x04)
        fout.write(content)# 5

        fout.write(fin_cont) #  6, append input file content
    
        content = struct.pack("I", (ga_b + 1) >> 16)  # Host driver(egret version) compatible
        fout.write(content)# 7
        content = struct.pack("I", (ga_b + 1) & 0x0000FFFF)  # Host driver(egret version) compatible
        fout.write(content)# 8
    elif( ga_f == 'tlv_data' ):
	    # Image header struct:
        #   1. Total Length (32 bit)
		#   2. Patch Length (32 bit)
		#   3. Signing Format Version (8 bit)
		#   4. Signature Algorithm (8 bit)
		#   5. Image Type (8 bit)
		#   6. product ID (16 bit)
        #   7. Build version (16 bit)
        #   8. Patch version (16 bit)
        #   9. Reserved (16 bit)
        #   10. Anti-Rollback Version (32 bit)
        #   11. Entry_addr (32 bit)
        #   12. Patch Payload (Variable)
        #   13. Signature (Variable)
        #   14. Public Key (256 byte)
        if(ga_tlv_sign_algo == 2):
            ga_s = os.path.getsize(ga_i)
            # Total Length of the TLV Data including Patch Header and Patch Size
            content = struct.pack("I", ga_s + 28)
            fout.write(content)# 1
            # Length of Patch Size with CRC 
            content = struct.pack("I", ga_s + 4)
            fout.write(content)# 2
            # Version of Signing Format
            content = struct.pack("B", ga_crc_ver)
            fout.write(content)# 3
            # Signature Algorithm Format
            content = struct.pack("B", ga_tlv_sign_algo)
            fout.write(content)# 4
            # Tlv Rsp Config
            content = struct.pack("B", ga_tlvrsp)
            fout.write(content)# 5.1            
            # Reserved0 of 1Bytes
            content = struct.pack("B", ga_image_type)
            fout.write(content)# 5.2
            # Product ID
            content = struct.pack("H", ga_t)
            fout.write(content)# 6
            # ROM Build Version 
            content = struct.pack("H", (((ga_b + 1) >> 16) % 65536))
            fout.write(content)# 7
            # Patch version 
            content = struct.pack("H", ((ga_b + 1) % 65536))
            fout.write(content)# 8
            # Reserved1 of 2Bytes
            content = struct.pack("H", ((ga_patch_ctl >> 16) % 65536))
            fout.write(content)# 9
            # Anti-rollback version
            content = struct.pack("I", ga_anti_rollback_version)
            fout.write(content)# 10
            # Patch Entry Address
            content = struct.pack("I", ga_j)
            fout.write(content)# 11
            # Patch Data
            fout.write(fin_cont)# 12
            # CRC of Patch Data
            crc32 = (~binascii.crc32(fin_cont)) & 0xFFFFFFFF
            #print '%x' % crc32
            content = struct.pack("I", crc32)
            fout.write(content)# 13
        else:
            print 'Unsupported Signature!'
            usage()
            sys.exit(2)
    elif( ga_f == 'dev_signed_tlv' ):

			from Crypto.Signature import PKCS1_PSS
			from Crypto.Hash import SHA256
			from Crypto.PublicKey import RSA
			
			# TLV Type
			content = struct.pack("B", ga_tlv_type)
			fout.write(content)# 1
			# Length of the TLV Signed patch with Signature. 
			# Written as 3 Bytes
			ga_s = os.path.getsize(ga_i)
			ga_tlv_len = ga_s + 256 + 256 # Signature (256 bytes) and Public key
			byte_content = ga_tlv_len % 256
			content = struct.pack("B", byte_content)
			fout.write(content)# 2.1
			byte_content = (ga_tlv_len >> 8) % 256
			content = struct.pack("B", byte_content)
			fout.write(content)# 2.2
			byte_content = (ga_tlv_len >> 16) % 256
			content = struct.pack("B", byte_content)
			fout.write(content)# 2.3
            # Patch data with Patch Header and Code
			fout.write(fin_cont)
            # Patch Signature
			privateKey = RSA.importKey(open('rome_dev_rsa.pem').read())
			hash = SHA256.new()
			hash.update(fin_cont)
			print(hash.hexdigest())

			fout_hash_name = fout.name[:-15] + '.hash'
			fout_hash = open(fout_hash_name, "w")
			fout_hash.write(hash.hexdigest())
			fout_hash.close()

			signer = PKCS1_PSS.new(privateKey)
			signature = signer.sign(hash)
            
			fout.write(signature)
			fout.write(open('rome_dev_rsa.pub').read())

    elif ( ga_f == 'tuncate' ):
    	file = open(ga_i, 'rb')
        content = file.read(ga_l)
        fout.write(content)
        file.close()

    else:
        # Image header struct:
        #   1. product ID
        #   2. patch version (16 bit)
        #   3. build version (16 bit)
        #   4. load_addr,
        #   5. file_length,
        #   6. entry_addr,
        #   7. crc32
        #   8. image type
        content = struct.pack("I", ga_t)
        fout.write(content)# 1
        # content = struct.pack("H", ga_p)
        # fout.write(content)# 1
        content = struct.pack("I", ga_b + 1) # Patch BuildVer is 1 Plus Rom BuildVer 
        fout.write(content)# 1
        content = struct.pack("I", ga_l)
        fout.write(content)# 1
        content = struct.pack("I", ga_j)
        fout.write(content)# 3
        content = struct.pack("I", os.path.getsize(ga_i))
        fout.write(content)# 2
        crc32 = (~binascii.crc32(fin_cont)) & 0xFFFFFFFF
        #print '%x' % crc32
        content = struct.pack("I", crc32)
        fout.write(content)# 4
        content = struct.pack("I", 0x80000000)
        fout.write(content)# 5
        fout.write(fin_cont) # 6 append input file content

    fout.flush()
    fout.close()
    fin.close()
    

if __name__ == '__main__':
	main();

# vim: set ts=4: tw=4: sts=4:
