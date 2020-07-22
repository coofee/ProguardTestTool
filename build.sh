#!/usr/bin/env bash

#version=6.0.3

version=$1

echo "try download proguard version=$version to proguard-$version.zip"
@curl "https://codeload.github.com/Guardsquare/proguard/zip/proguard$version" -o "proguard-$version.zip"

echo "try unzip proguard-$version.zip..."
unzip "proguard-$version.zip" -d .

echo "try copy proguard-proguard$version to current dir..."
mv "proguard-proguard$version" proguard

echo "try mkdir lib..."
cd proguard
mkdir lib

echo "cd to buildscripts"
cd buildscripts

echo "try build proguard..."
./build.sh

echo "build done."

