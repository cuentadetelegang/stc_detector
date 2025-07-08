#!/usr/bin/env bash
# Parchea jnius_utils.pxi para reemplazar “long” por “int”
find .buildozer/android/platform -path "*/pyjnius*/jnius/jnius_utils.pxi" \
    -exec sed -i 's/isinstance(arg, long)/isinstance(arg, int)/g' {} \;
