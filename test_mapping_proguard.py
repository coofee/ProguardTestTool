#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import sys;

def filterMappingClassName(line):
    if len(line) <=0 or line.startswith("    ") or line.find(":") <= 0:
        return None, None

    end = line.find(":")
    splits = line[0:end].split(" -> ")
    originClassName = splits[0]
    obfuscateClassName = splits[1]
    obfuscated = False
    if originClassName != obfuscateClassName:
        sys.stderr.write("{} obfuscate to {}\n".format(originClassName, obfuscateClassName))
        obfuscated = True
    else:
        obfuscated = False
    return obfuscateClassName, obfuscated

def parseMappingFile(mappingFile, classListFile):
    try:
        classListFileWriter = open(classListFile, "w")
        with open(mappingFile) as fp:
            classCount = 0
            obfuscatedClassCount = 0
            for index, line in enumerate(fp):
                className, obfuscated = filterMappingClassName(line)
                if className is not None:
                    classCount += 1
                    if obfuscated:
                        obfuscatedClassCount += 1
                    classListFileWriter.write(className)
                    classListFileWriter.write('\n')
            sys.stderr.write("mapping file have {} class, obfuscated {} class.\n".format(classCount, obfuscatedClassCount))
            if obfuscatedClassCount == 0:
                sys.stderr.write(u"未混淆\n")
            else:
                sys.stderr.write(u"已混淆\n")
    finally:
        classListFileWriter.close()

if __name__ == '__main__':
    mappingFile = sys.argv[1]
    parseMappingFile(mappingFile, "class.list.txt")

