#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import sys
import os
import datetime

DEBUG = False

def printToStdout(dataList):
    for index, data in enumerate(dataList):
        sys.stdout.write(data)
        sys.stdout.write('\n')

def log(str):
    if DEBUG:
        print(str)

def readlines(file):
    with open(file, 'r') as fp:
        return fp.readlines()

def writeToFile(dataList, destFile, mode="w"):
    try:
        writer = open(destFile, mode)
        for index, data in enumerate(dataList):
            log(data)
            writer.write(data)
        writer.flush()
        os.fsync(writer.fileno())
    finally:
        writer.close()


def popen(command):
    stream = os.popen(command)
    return stream.readlines()

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
    """
    @param mappingFile mapping.txt file.
    @param classListFile mapping class name.
    @return true, if obfuscated; otherwise return false.
    """
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
                return False
            else:
                sys.stderr.write(u"已混淆\n")
                return True
    finally:
        classListFileWriter.close()

    return False

def parseProguardRulesFile(proguardRulesFile):
    rules = []
    with open(proguardRulesFile, "r") as fp:
        rule = ""
        for index, line in enumerate(fp):
            if line is None:
                continue
            
            lineStrip = line.strip()
            if len(lineStrip) < 1:
                continue

            indexOfCommentChar = lineStrip.find('#')
            if indexOfCommentChar == 0:
                continue
            
            if indexOfCommentChar > 0:
                lineStrip = lineStrip[0:indexOfCommentChar]

            # log("lineStrip={}".format(lineStrip))

            if lineStrip[0] == '-':
                if rule is not None and len(rule) > 1:
                    # log("rule={}".format(rule))
                    rules.append(rule + '\n')
                rule = lineStrip
            else:
                rule += '\n' + lineStrip

        if rule is not None and len(rule) > 1:
            rules.append(rule)

        log("proguard rules file contains {} rule.".format(len(rules)))

    return rules

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

def generateProguardBaseConfigFile(fileList):
    baseConfigFile = "proguard_base_config.txt"

    try:
        writer = open(baseConfigFile, "w")
        for index, file in enumerate(fileList):
            for i, line in enumerate(readlines(file)):
                writer.write(line)
        writer.flush()
    finally:
        writer.close()

    print("generate proguard base config file={}".format(baseConfigFile))
    return baseConfigFile


INDEX = 0

def proguard(baseConfigFile, rules, start, end):
    if start == end:
        return True

    global ERROR_RULES
    currentRules = set(rules[start:end]) - ERROR_RULES
    if len(currentRules) == 0:
        return True

    global INDEX
    INDEX += 1

    localIndex = INDEX
    configFile = "proguard_config_{index}_{start}_{end}.txt".format(index=localIndex, start=start, end=end)
    writeToFile(readlines(baseConfigFile), configFile, "w")

    writeToFile(currentRules, configFile, "a")
    msg = "proguard#{index} with {configFile}, rule.start={start}, rule.end={end}\n".format(index=localIndex, configFile=configFile, start=start, end=end)
    print("try " + msg)
    exitCode = os.system("./proguard/bin/proguard.sh @{configFile}".format(configFile=configFile))
    if exitCode == 0:
        print("success " + msg)
        return parseMappingFile("mapping.txt", "class.list.{}.txt".format(localIndex))
    else:
        print("failed " + msg)
        return False

def testProguardRules(baseConfigFile, rules, start, end):
    if end - start == 1:
        print("proguardRecurse start={start}, end={end}".format(start=start, end=end))
        obfuscated = proguard(baseConfigFile, rules, start, end)
        if not obfuscated:
            errorRuleFile = "proguard_error_rules.txt"
            errorRule = rules[start]
            print("proguardRecurse error rule={rule}".format(rule=errorRule))
            writeToFile([errorRule], errorRuleFile, "a+")

    elif end - start == 2:
        testProguardRules(baseConfigFile, rules, start, start + 1)
        testProguardRules(baseConfigFile, rules, start + 1, end)

    else:
        print("proguardRecurse start={start}, end={end}".format(start=start, end=end))
        obfuscated = proguard(baseConfigFile, rules, start, end)
        if not obfuscated:
            mid = int((start + end) / 2)
            testProguardRules(baseConfigFile, rules, start, mid)
            testProguardRules(baseConfigFile, rules, mid, end)

def enumerateTest():
    global ERROR_RULES
    errorRuleFile = "proguard_error_rules.txt"
    for index, rule in enumerate(rules):
        obfuscated = proguard(baseConfigFile, rules, 0, index)
        if not obfuscated:
            ERROR_RULES.add(rule)
            writeToFile(ERROR_RULES, errorRuleFile, "a+")

ERROR_RULES = set()

def test(baseConfigFile, rules):
    if len(rules) < 1:
        print("test no rules.")
        return

    testProguardRules(baseConfigFile, rules, 0, len(rules))
    # proguardRecurse(baseConfigFile, rules, 3, 4)
    # proguardRecurse(baseConfigFile, rules, 0, len(rules))
    # enumerateTest()
    errorRules = readlines("proguard_error_rules.txt")
    if len(errorRules) > 0:
        print(u"混淆错误配置如下：")
        printToStdout(readlines("proguard_error_rules.txt"))
    else:
        print(u"混淆配置OK.")


if __name__ == '__main__':
    starttime = datetime.datetime.now()

    command = sys.argv[1]

    if "mapping" == command:
        mappingFile = sys.argv[2]
        parseMappingFile(mappingFile, "class.list.txt")

    elif "rule" == command:
        ruleFile = sys.argv[2]
        rules = parseProguardRulesFile(ruleFile)
        printToStdout(rules)

    elif "config" == command:
        configFile = sys.argv[2] if len(sys.argv) > 2 else "config.txt"
        parseConfigFile(configFile)

    elif "test" == command:
        # injars = popen("cat config.txt | grep '\-injars'")
        # writeToFile(injars, "proguard_injars.txt")

        # libraryjars = popen("cat config.txt | grep '\-libraryjars'")
        # writeToFile(injars, "proguard_libraryjars.txt")
        # outputConfigFile = sys.argv[2] if len(sys.argv) > 2 else "proguard_output_config.txt"
        # ruleMinifyFile = sys.argv[3] if len(sys.argv) > 3 else "proguard_rules_minify.txt"
        # rulesFile = sys.argv[4] if len(sys.argv) > 4 else "proguard_rules.txt"

        injarsFile = "proguard_injars.txt"
        libraryjarsFile = "proguard_libraryjars.txt"
        outputConfigFile = "proguard_output_config.txt"
        ruleMinifyFile = "proguard_rules_minify.txt"
        baseConfigFile = generateProguardBaseConfigFile([injarsFile, libraryjarsFile, outputConfigFile, ruleMinifyFile])

        rulesFile = "proguard_rules.txt"
        rules = parseProguardRulesFile(rulesFile)
        test(baseConfigFile, rules)

    elif "append" == command:
        testAppendFile = "test_append.txt"
        testData = "ddd"
        writeToFile(["aaa"], testAppendFile, "a+")
        writeToFile(["bbb"], testAppendFile, "a+")
        writeToFile(["ccc"], testAppendFile, "a+")
        writeToFile([testData], testAppendFile, "a+")

    else:
        print("NOT SUPPORT {}".format(command))

    endtime = datetime.datetime.now()
    print("consume {} seconds\n".format((endtime - starttime).seconds))


