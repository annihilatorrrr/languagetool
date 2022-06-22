#!/usr/bin/env python3
# coding: utf-8

import os
import sys

"""
Program creates list of SQL UPDATE statements to label words in database
according to different dialects of Serbian language. Input file has format
of

label   wordform    lemma

Items are separated with one or more <TAB> characters.
"""

# Returns SQL UPDATE statement
def getUpdateStatement(dialect, wordform, lemma):
    return f"UPDATE words SET dialect='{dialect}' WHERE wordform='{wordform}' AND lemma='{lemma}';\n".encode(
        'utf-8'
    )


if __name__ == "__main__":
    inputFile = sys.argv[1]
    if not os.path.exists(inputFile):
        print(f"(EE) Input file '{inputFile}' does not exist, aborting")
        sys.exit(1)
    with open("out.txt", "wb") as outF:
        # Dialect indicator - if 'e' or 'i' create UPDATE statements
        dialect = None
        ekavianLabels = ('Е', 'е', 'E', 'e',)
        jekavianLabels = ('И', 'и', 'I', 'i',)
        validDialects = ekavianLabels + jekavianLabels

        with open(inputFile) as f:
            for line in f:
                line = line.strip()
                if line in (None, ''):
                    dialect = None
                    continue
                tokens = line.split()
                if len(tokens) == 3:
                                    # Line with dialect indicator
                    if tokens[0] in validDialects:
                        if tokens[0] in ekavianLabels:
                            dialect = 'e'
                        elif tokens[0] in jekavianLabels:
                            dialect = 'i'
                        else:
                            print(
                                f"(WW) Unknown dialect '{tokens[0]}' where wordform='{tokens[1]}' and lemma='{tokens[2]}'"
                            )

                            continue
                        outF.write( getUpdateStatement(dialect, tokens[1], tokens[2]))
                    else:
                        dialect = None
                elif len(tokens) == 2:
                    # Word form and lemma, check dialect
                    if dialect in validDialects:
                        outF.write( getUpdateStatement(dialect, tokens[0], tokens[1]))
                else:
                    print(f"(WW) Unknown line form, skipping: '{line}'")
                    continue
            f.close()