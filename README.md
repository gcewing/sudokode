Sudokode
========

*Problem:* You are a spy who wants to smuggle small amounts of
information out of the country.

*Solution:* Get a job creating sudoku puzzles for a newspaper,
and use this program.

What it does
------------
Takes text and encodes it in the form of sudoku grids, and the
reverse. Generates either puzzles or filled-in grids.

Limitations
-----------

* Input restricted to 7-bit ASCII characters.
* Only decodes filled-in grids. Puzzles must be solved by the
  user before decoding.

Why did I write it?
-------------------

Inspired by a comment on 3blue1brown's video about Hamming codes that
likened them to sudoku puzzles, and a reply pointing out that sudoku
puzzles don't carry any information. I set out to remedy that.

Video: https://www.youtube.com/watch?v=X8jsijhllIA

Usage
-----
```
Usage: sudokode.py (-e [-p] [-s] | -d | -t) [-D] < input > output
Options:
  -h, --help    show this help message and exit
  -e, --encode  read plain text from stdin and write sudoku grids to stdout
  -d, --decode  read sudoku grids from stdin and write plain text to stdout
  -p, --puzzle  generate puzzle grids instead of filled-in grids
  -t, --test    run a brief internal test
  -s, --stats   report encoding statistics
  -D, --debug   write debugging information to stderr
```

Example
-------
```
% cat plain.txt
THE MISSILES ARE HIDDEN IN IDAHO
% sudokode.py -e < plain.txt > secret.txt
% cat secret.txt
+---+---+---+
|586|129|347|
|124|837|965|
|793|465|182|
+---+---+---+
|915|678|234|
|637|942|851|
|248|351|679|
+---+---+---+
|369|714|528|
|451|283|796|
|872|596|413|
+---+---+---+

+---+---+---+
|817|249|536|
|935|876|421|
|246|351|879|
+---+---+---+
|678|423|195|
|392|615|784|
|154|987|263|
+---+---+---+
|761|592|348|
|429|138|657|
|583|764|912|
+---+---+---+

+---+---+---+
|896|412|753|
|317|589|462|
|452|367|198|
+---+---+---+
|539|726|841|
|684|931|527|
|271|845|936|
+---+---+---+
|768|294|315|
|923|158|674|
|145|673|289|
+---+---+---+

+---+---+---+
|945|816|327|
|123|457|689|
|678|239|145|
+---+---+---+
|214|365|798|
|356|798|214|
|789|124|536|
+---+---+---+
|437|581|962|
|561|942|873|
|892|673|451|
+---+---+---+

% sudokode.py -d < secret.txt
THE MISSILES ARE HIDDEN IN IDAHO
%
```
