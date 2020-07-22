#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import os

def execCommand(command):
    exitCode = os.system(command)
    if exitCode == 0:
        print("success execute " + command)
        return True
    else:
        print("failed execute " + command)
        return False

def parseConfigFile(configFile = "config.txt"):
    injarsFile = "proguard_injars.txt"
    execCommand("cat {configFile} | grep '\-injars' > {outFile}".format(configFile=configFile, outFile=injarsFile))

    libraryjarsFile = "proguard_libraryjars.txt"
    execCommand("cat {configFile} | grep '\-libraryjars' > {outFile}".format(configFile=configFile, outFile=libraryjarsFile))

    outputConfigFile = "proguard_output_config.txt"
    try:
        writer = open(outputConfigFile, "w")
        writer.write("""-dump class_files.txt
    -outjars 0.jar
    -printconfiguration config-tmp.txt
    -printmapping mapping.txt
    -printusage usage.txt
    -printseeds seeds.txt""")
        writer.flush()
    finally:
        writer.close()

    noInputOptionsFile = "proguard_no_libraryjars_and_injars.txt"
    tmpNoInputOptionsFile = "proguard_no_libraryjars_and_injars.txt.tmp"
    execCommand("cat {configFile} | grep -v '\-injars' > {outFile}".format(configFile=configFile, outFile=tmpNoInputOptionsFile))
    execCommand("cat {inputFile} | grep -v '\-libraryjars' > {outFile}".format(inputFile=tmpNoInputOptionsFile, outFile=noInputOptionsFile))
    
if __name__ == '__main__':
    parseConfigFile()
