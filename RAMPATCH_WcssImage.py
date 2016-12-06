#===============================================================================
#
# Bluetooth CPU build script
#
# GENERAL DESCRIPTION
#    RAMPATCH build script
#
# Copyright (c) 2012, 2015 by Qualcomm Technologies, Incorporated.
# All Rights Reserved.
# QUALCOMM Proprietary and Confidential
#
#-------------------------------------------------------------------------------
#
#  $Header: $
#  $DateTime: $
#  $Author: $
#  $Change: $
#
#===============================================================================
from SCons.Script import *
import wcss_utils

#------------------------------------------------------------------------------
# Hooks for Scons
#------------------------------------------------------------------------------
def exists(env):
   return env.Detect('CoreImage CPU')

def generate(env):
   buildspec = str(env.GetOption('buildspec'))
   BUILDSPEC = os.environ.get('BUILDSPEC')
   #------------------------------------------------------------------------------
   # Decide build steps
   #------------------------------------------------------------------------------
   # regular build steps (no filter) is build everything, once a user start 
   # using filters we have to make decisions depending on user input.
   # The LoadAUSoftwareUnits function will take care of filtering subsystem, units, 
   # etc. This is to take care of what steps to enable disable from the top level
   # script, such as building files specify in this script i.e. quatz, stubs, etc.
   do_local_files = True
   do_link = True
   do_post_link = True

   # MACROS for TLV RSP Config; If BIT0 set NO ACK for VSE; If BIT1 set NO ACK for CC 
   TLV_RSP_CFG_ACK_CC_ACK_VSE = 0
   TLV_RSP_CFG_ACK_CC_NO_VSE  = 1
   TLV_RSP_CFG_NO_CC_ACK_VSE  = 2
   TLV_RSP_CFG_NO_CC_NO_VSE   = 3

   # get user input from command line
   filter_opt = env.get('FILTER_OPT')
   elf_file = ARGUMENTS.get('process_elf', None)
   
   # make decisions
   if filter_opt is not None:
      do_link = False
      
      if env.FilterMatch(os.getcwd()):
         if elf_file:
            image_elf = File(elf_file)
         else:
            do_post_link = False
      else:
         do_local_files = False
         do_post_link = False

   #-------------------------------------------------------------------------
   # Libs/Objs
   #-------------------------------------------------------------------------
   image_libs_path = env.get('INSTALL_LIBPATH')
   image_libs = env.get('WCSS_RAMPATCH_LIBS')
   image_objs = env.get('WCSS_RAMPATCH_OBJS')

   image_units = [image_libs, image_objs]

   if do_local_files:
      # make our clone so we won't mess the lib rules, it shoun't because they 
      # should of clone, but just to be on the safe side.
      env = env.Clone()

      #=========================================================================
      # Begin building WCSS
      #

      #----------------------------------------------------------------------------
      # Build env scatter load
      #----------------------------------------------------------------------------
      target_scl = env.SclBuilder("${SHORT_BUILDPATH}/${WCSS_SUBDIR}/${TARGET_NAME}_rampatch", [
         "${BUILD_MS_ROOT}/${BUILD_ASIC}_rampatch.scl"
      ])

      image_units += target_scl

      #----------------------------------------------------------------------------
      # Sources, libraries
      #----------------------------------------------------------------------------

   if do_link:
      # actually doing link, reset image_units
      image_units = []
      
      if env['CHIPSET'] in ['QCA6174']:
          env.Append(SYS_PROD_ID = '0x00000008')
      if env['CHIPSET'] in ['QCA3685']:
          env.Append(SYS_PROD_ID = '0x00000009')
      if env['CHIPSET'] in ['WCN3990']:
          env.Append(SYS_PROD_ID = '0x0000000A')
      if env['CHIPSET'] in ['QCA6290']:
          env.Append(SYS_PROD_ID = '0x0000000D')

      #-------------------------------------------------------------------------
      # Build env WCSS
      #-------------------------------------------------------------------------

      # Pass LINKCOM to SCONS. FIXME: Fix this hardcore way.
      # 1. Put --entry patch_entry after $LINKFLAGS to overwritten defautl value.
      # 2. Import ROM symbol as input file

      # generate ELF
      env.Append(PATCH_LINKCOM = "$LINK $LINKFLAGS --entry patch_entry \
                                  ${SHORT_BUILDPATH}/${TARGET_NAME}.sym $_LISTFILES $SOURCES $ARMLD_OUTPUT_CMD $TARGET")
      if buildspec != 'none' or BUILDSPEC is not None:
          env.Append(PATCH_LINKSTR = "=== Generating RAMPatch ELF image ${TARGET} &&& ${PATCH_LINKCOM}")
      else:
          env.Append(PATCH_LINKSTR = "=== Generating RAMPatch ELF image ${TARGET}")
      elf_act = SCons.Action.Action('$PATCH_LINKCOM', '$PATCH_LINKSTR')
      
      # generate TXT
      env.Append(TXT_TOOL = "$BINTOOL ${SHORT_BUILDPATH}/${WCSS_SUBDIR}/${TARGET_NAME}_rampatch.elf -c --output ${SHORT_BUILDPATH}/${WCSS_SUBDIR}/${TARGET_NAME}_rampatch.txt")
      if buildspec != 'none' or BUILDSPEC is not None:
         env.Append(TXT_TOOLSTR = "=== Generating Dessemble codes ${TARGET} &&& ${TXT_TOOL}")
      else:
         env.Append(TXT_TOOLSTR = "=== Generating Dessemble codes ${TARGET}")
      txt_act = SCons.Action.Action('$TXT_TOOL', '$TXT_TOOLSTR')  

      # generate SREC
      env.Append(SREC_TOOL = "$BINTOOL ${SHORT_BUILDPATH}/${WCSS_SUBDIR}/${TARGET_NAME}_rampatch.elf -m32 --output ${SHORT_BUILDPATH}/${WCSS_SUBDIR}/${TARGET_NAME}_rampatch.m32")
      if buildspec != 'none' or BUILDSPEC is not None:
         env.Append(SREC_TOOLSTR = "=== Generating SREC codes ${TARGET} &&& ${SREC_TOOL}")
      else:
         env.Append(SREC_TOOLSTR = "=== Generating SREC codes ${TARGET}")
      srec_act = SCons.Action.Action('$SREC_TOOL', '$SREC_TOOLSTR')

      # generate BIN
      env.Command('${SHORT_BUILDPATH}/${WCSS_SUBDIR}/${TARGET_NAME}_rampatch.bin', '${SHORT_BUILDPATH}/${WCSS_SUBDIR}/${TARGET_NAME}_rampatch.elf',  "$BINTOOL $SOURCE --bin --output $TARGET")
      
      # FIXME: hardcode -t 0x00000007 
      # Remove non TLV format
      #env.Append(RUN_HOSTTOOL = "$HOSTTOOL -t $SYS_PROD_ID \
      #                           -b ${RAMPATCH_BUILDVER} \
      #                           -j ${RAMPATCH_LINKADDR} \
      #                           -l ${RAMPATCH_LOADADDR} \
      #                           -i ${SHORT_BUILDPATH}/${WCSS_SUBDIR}/${TARGET_NAME}_rampatch.bin \
      #                           -o ${SHORT_BUILDPATH}/${WCSS_SUBDIR}/${TARGET_NAME}_rampatch.img\r\n")
      
      # TODO: how to remove bin and dfu image automatically?
      act = [elf_act, txt_act, srec_act]
      image_elf = env.AddProgram("${SHORT_BUILDPATH}/${WCSS_SUBDIR}/${TARGET_NAME}_rampatch",
                                 source=image_objs, LIBS=image_libs,
                                 LINKCOM=act)
      env.Depends(image_elf, target_scl)
      env.Depends(image_elf, '${SHORT_BUILDPATH}/${TARGET_NAME}.sym')

      # HostTool Environment 
      env.Replace(HOSTTOOL_FILE = env.RealPath("${BUILD_SCRIPTS_ROOT}/hosttool.py"))   
      env.Replace(HOSTTOOL = "${PYTHONCMD} ${HOSTTOOL_FILE}")               
      env.Replace(RUN_HOSTTOOL = "$HOSTTOOL -t ${SYS_PROD_ID} \
                                 -b ${RAMPATCH_BUILDVER} \
                                 -x ${IMAGE_TYPE} \
                                 -s ${ANTIROLLBACK_VER} \
                                 -j ${RAMPATCH_LINKADDR} \
                                 -l ${RAMPATCH_LOADADDR}")
       # generate TLV payload
      env.Replace(TLV_RSP_CFG = TLV_RSP_CFG_ACK_CC_ACK_VSE)  
      env.Command('${SHORT_BUILDPATH}/${WCSS_SUBDIR}/${TARGET_NAME}_rampatch_data.bin', '${SHORT_BUILDPATH}/${WCSS_SUBDIR}/${TARGET_NAME}_rampatch.bin',  "$RUN_HOSTTOOL -i $SOURCE -f tlv_data -a $TLV_RSP_CFG -o $TARGET")
      
      env.Replace(TLV_RSP_CFG_OPT = TLV_RSP_CFG_NO_CC_NO_VSE)  
      env.Command('${SHORT_BUILDPATH}/${WCSS_SUBDIR}/${TARGET_NAME}_rampatch_data_opt.bin', '${SHORT_BUILDPATH}/${WCSS_SUBDIR}/${TARGET_NAME}_rampatch.bin',  "$RUN_HOSTTOOL -i $SOURCE -f tlv_data -a $TLV_RSP_CFG_OPT -o $TARGET")

      if not env.GetOption('dis_siggen'):
         tgt_tlvdata = env.Command('${SHORT_BUILDPATH}/${WCSS_SUBDIR}/${TARGET_NAME}_rampatch_dev_signed.tlv', '${SHORT_BUILDPATH}/${WCSS_SUBDIR}/${TARGET_NAME}_rampatch_data.bin',  "$RUN_HOSTTOOL -i $SOURCE -f dev_signed_tlv -o $TARGET")
         tgt_tlvdata += env.Command('${SHORT_BUILDPATH}/${WCSS_SUBDIR}/${TARGET_NAME}_rampatch_dev_signed_opt.tlv', '${SHORT_BUILDPATH}/${WCSS_SUBDIR}/${TARGET_NAME}_rampatch_data_opt.bin',  "$RUN_HOSTTOOL -i $SOURCE -f dev_signed_tlv -o $TARGET")
      # generate DFU   
      tgt_dfu = env.Command('${SHORT_BUILDPATH}/${WCSS_SUBDIR}/${TARGET_NAME}_rampatch.dfu', '${SHORT_BUILDPATH}/${WCSS_SUBDIR}/${TARGET_NAME}_rampatch.bin',  "$RUN_HOSTTOOL -i $SOURCE -f dfu -o $TARGET")      
      
      image_units += [
         tgt_tlvdata, tgt_dfu
      ]           

   if do_post_link:      
      #-------------------------------------------------------------------------
      # Install ELF, reloc files
      #-------------------------------------------------------------------------

      # copy elf and reloc to needed locations for AMSS tools to load on target
      install_target_elf = env.InstallAs(
         "${BUILD_MS_ROOT}/${TARGET_NAME}_${WCSS_SUBDIR}.elf", image_elf)
      
      patchinfo = env.Command('patchinfo_${WCSS_SUBDIR}', '${SHORT_BUILDPATH}/${WCSS_SUBDIR}/${TARGET_NAME}_rampatch.map', wcss_utils.wcss_log_patchinfo)
      env.Depends(patchinfo, tgt_tlvdata)
      #=========================================================================
      # Define targets needed WCSS
      #
      image_units += [
         install_target_elf, patchinfo
      ]
      
   # add aliases
   aliases = env.get('IMAGE_ALIASES')
   for alias in aliases:
      env.Alias(alias, image_units)

