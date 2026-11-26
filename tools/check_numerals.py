#!/usr/bin/env python3
"""Checks that OmegaT reads every numeral sample of slide 6 as the value the
deck claims (NUMERALS: 2345, NUMBER_SIGNS: their value). Runs
org.omegat.util.NumeralValueParser.parseValue from an OmegaT installation
that contains it (numeral-check work) through jshell.

    OMEGAT_HOME=/path/to/OmegaT python3 tools/check_numerals.py

OMEGAT_HOME is the folder holding OmegaT.jar and lib/. Exit status 1 if any
sample is not read as claimed.

@author stephan.pakebusch at zollsoft.de
"""
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from deck_content import NUMBER_SIGNS, NUMERALS  # noqa: E402

home = os.environ.get("OMEGAT_HOME") or sys.exit("set OMEGAT_HOME to an OmegaT installation folder")
rows = [(k, t, "2345") for k, t, *_ in NUMERALS] + [(k, t, v) for k, t, v, *_ in NUMBER_SIGNS]
with tempfile.TemporaryDirectory() as tmp:
    tsv = os.path.join(tmp, "samples.tsv")
    with open(tsv, "w", encoding="utf-8") as f:
        f.writelines(f"{k}\t{t}\t{v}\n" for k, t, v in rows)
    script = os.path.join(tmp, "check.jsh")
    with open(script, "w", encoding="utf-8") as f:
        f.write('import org.omegat.util.NumeralValueParser;\n'
                'int bad = 0;\n'
                f'for (String line : java.nio.file.Files.readAllLines(java.nio.file.Path.of("{tsv}"))) {{\n'
                '  String[] p = line.split("\\t");\n'
                '  String got = NumeralValueParser.parseValue(p[1]).map(Object::toString).orElse("-");\n'
                '  boolean ok = got.equals(p[2]);\n'
                '  if (!ok) bad++;\n'
                '  System.out.println((ok ? "ok   " : "FAIL ") + p[0] + "\\t" + p[1] + "\\t" + got);\n'
                '}\n'
                '/exit bad == 0 ? 0 : 1\n')
    cp = os.pathsep.join([os.path.join(home, "OmegaT.jar"), os.path.join(home, "lib", "*")])
    r = subprocess.run(["jshell", "--class-path", cp, "-R-Dstdout.encoding=UTF-8", "-q", script],
                       stdin=subprocess.DEVNULL, timeout=300)
    sys.exit(r.returncode)
