#!/usr/bin/env python3
#---------------------------------------------------------------------------
#
#   Sudokode - Encode and decode text in the form of sudoku grids.
#
#---------------------------------------------------------------------------

import optparse, sys, random
from math import log2

class SudokuError(ValueError):
  pass

alphabet = ('1', '2', '3', '4', '5', '6', '7', '8', '9')

divider = "+---" * 3 + "+"

def hash_row(row):
  return sum(i * ord(c) for i, c in enumerate(row))

def hash_rows(rows):
  return sum(i * hash_row(row) for i, row in enumerate(rows))

def print_info(*args, **kwds):
  print(file = sys.stderr, *args, **kwds)

def format(rows):
  result = []
  for r, row in enumerate(rows):
    if r % 3 == 0:
      result.append(divider)
    line = "".join(row)
    result.append("|%s|%s|%s|" % (line[:3], line[3:6], line[6:]))
  result.append(divider)
  return "\n".join(result)

def unformat(text):
  chars = []
  for c in text:
    if "1" <= c <= "9":
      chars.append(c)
    elif c in "+-|\n":
      pass
    elif c == ' ':
      raise SudokuError("Unsolved sudoku grid (must be solved before decoding)")
    else:
      raise SudokuError("Invalid character %r in sudoku grid" % c)
  if len(chars) != 81:
    raise SudokuError("Wrong number of digits in sudoku grid")
  return [chars[i:i+9] for i in range(0, 81, 9)]

def read_grid(f):
  lines = []
  while True:
    line = f.readline().strip()
    if not line:
      break
    lines.append(line)
  if lines:
    return unformat("".join(lines))

def dump(rows):
  print_info(format(rows))

def square_containing_cell(r, c):
  return (r // 3) * 3 + c // 3

def cell_indices(n):
  r, c = divmod(n, 9)
  s = square_containing_cell(r, c)
  return r, c, s

def cells_in_same_square(r, c):
  r0 = r - (r % 3)
  c0 = c = (c % 3)
  for r1 in range(r0, r0 + 3):
    for c1 in range(c0, c0 + 3):
      yield (r1, c1)

class Stats:

  def __init__(self):
    self.chars = 0
    self.blocks = 0
    self.entropy_used = 0.0
    self.entropy_unused = 0.0
    self.removed1 = 0
    self.removed2 = 0

class Coder:

  debug = False

  def __init__(self, options = None, stats = None):
    self.stats = stats
    if options:
      self.debug = getattr(options, "debug", False)
      self.puzzle_mode = getattr(options, "puzzle_mode", False)
  
  def alphabet_sets(self):
    return [set(alphabet) for i in range(9)]
  
  def init_block(self):
    aset = self.alphabet_sets
    self.row_avail_sets = aset()
    self.col_avail_sets = aset()
    self.sqr_avail_sets = aset()

  def dprint(self, *args, **kwds):
    if self.debug:
      print_info(*args, **kwds)

  def available_symbols(self, r, c, s):
    row_avail = self.row_avail_sets[r]
    col_avail = self.col_avail_sets[c]
    sqr_avail = self.sqr_avail_sets[s]
    return row_avail & col_avail & sqr_avail

  def use_symbol(self, r, c, s, symbol):
    self.row_avail_sets[r].remove(symbol)
    self.col_avail_sets[c].remove(symbol)
    self.sqr_avail_sets[s].remove(symbol)
  
  def unuse_symbol(self, r, c, s, symbol):
    self.row_avail_sets[r].add(symbol)
    self.col_avail_sets[c].add(symbol)
    self.sqr_avail_sets[s].add(symbol)

  def find_candidate_list(self, n):
    r, c, s, = cell_indices(n)
    candidate_set = set()
    for symbol in self.available_symbols(r, c, s):
      self.dprint("considering", symbol)
      self.use_symbol(r, c, s, symbol)
      if self.solution_exists(n + 1):
        candidate_set.add(symbol)
      self.unuse_symbol(r, c, s, symbol)
    return sorted(candidate_set)

  def solution_exists(self, n):
    self.dprint("solution_exists(%s)" % n)
    if n == 81:
      self.dprint("found")
      return True
    else:
      r, c, s, = cell_indices(n)
      avail_set = self.available_symbols(r, c, s)
      for symbol in avail_set:
        self.use_symbol(r, c, s, symbol)
        success = self.solution_exists(n + 1)
        self.unuse_symbol(r, c, s, symbol)
        if success:
          return True
      return False

  def encode_block(self, bits):
    self.dprint("encoding bits: ", bits)
    self.init_block()
    rows = [[' '] * 9 for i in range(9)]
    self.chunks = []
    stats = self.stats
    if stats:
      stats.blocks += 1
    for n in range(81):
      r, c, s, = cell_indices(n)
      self.dprint("row %s col %s sqr %s" % (r, c, s))
      candidate_list = self.find_candidate_list(n)
      m = len(candidate_list)
      self.dprint("m =", m)
      if stats:
        e = log2(m)
        if bits:
          stats.entropy_used += e
        else:
          stats.entropy_unused += e
      bits, digit = divmod(bits, m)
      self.dprint("bits, digit = %s, %s" % (bits, digit))
      self.chunks.append((m, digit))
      symbol = candidate_list[digit]
      rows[r][c] = symbol
      self.use_symbol(r, c, s, symbol)
      if self.debug:
        dump(rows)
    self.dprint("encoded chunks =", self.chunks)
    if self.puzzle_mode:
      self.puzzlify(rows)
    return (rows, bits)
  
  def single_choice_available(self, r, c, s):
    return len(self.available_symbols(r, c, s)) == 1

  def row_position_unique(self, rows, r, c, s, symbol):
    for c1 in range(9):
      if c1 != c and rows[r][c1] == ' ':
        s1 = square_containing_cell(r, c1)
        avail = self.available_symbols(r, c1, s1)
        if symbol in avail:
          self.dprint("%r could also be in row %s at column %s" % (symbol, r, c1))
          return False
    self.dprint("rule 2: no other position in row %s for %r" % (r, symbol))
    return True

  def col_position_unique(self, rows, r, c, s, symbol):
    for r1 in range(9):
      if r1 != r and rows[r1][c] == ' ':
        s1 = square_containing_cell(r1, c)
        avail = self.available_symbols(r1, c, s1)
        if symbol in avail:
          self.dprint("%r could also be in column %s at row %s" % (symbol, c, r1))
          return False
    self.dprint("rule 2: no other position in column %s for %r" % (c, symbol))
    return True

  def sqr_position_unique(self, rows, r, c, s, symbol):
    for r1, c1 in cells_in_same_square(r, c):
      if r1 != r and c1 != c and rows[r1][c1] == ' ':
        avail = self.available_symbols(r1, c1, s)
        if symbol in avail:
          self.dprint("%r could also be in square %s at (%s, %s)" % (symbol, s, r1, c1))
          return False
    self.dprint("rule 2: no other position in square %s for %r" % (s, symbol))
    return True

  def puzzlify(self, rows):
    stats = self.stats
    seed = hash_rows(rows)
    random.seed(seed)
    removal_order = list(range(81))
    random.shuffle(removal_order)
    for n in removal_order:
      r, c, s, = cell_indices(n)
      symbol = rows[r][c]
      rows[r][c] = '*'
      self.unuse_symbol(r, c, s, symbol)
      if self.debug:
        dump(rows)
      self.dprint("puzzlify: considering %r at (%s, %s)" % (symbol, r, c))
      if self.single_choice_available(r, c, s):
        self.dprint("rule 1: no other choice")
        rows[r][c] = ' '
        if stats:
          stats.removed1 += 1
      elif (
          self.row_position_unique(rows, r, c, s, symbol)
          or self.col_position_unique(rows, r, c, s, symbol)
          or self.sqr_position_unique(rows, r, c, s, symbol)
      ):
        rows[r][c] = ' '
        if stats:
          stats.removed2 += 1
      else:
        rows[r][c] = symbol
        self.use_symbol(r, c, s, symbol)

  def decode_block(self, rows, chunks):
    self.init_block()
    for n in range(81):
      r, c, s, = cell_indices(n)
      self.dprint("row %s col %s sqr %s" % (r, c, s))
      candidate_list = self.find_candidate_list(n)
      m = len(candidate_list)
      self.dprint("m =", m)
      symbol = rows[r][c]
      digit = candidate_list.index(symbol)
      chunks.append((m, digit))
      self.use_symbol(r, c, s, symbol)
    
  def iter_encode_string(self, message):
    stats = self.stats
    if stats:
      stats.chars = len(message)
      stats.bits = 7 * stats.chars
    bits = 0
    for char in message:
      code = ord(char)
      if code > 0x7f:
        raise SudokuError("Non-ASCII character: %r" % char)
      bits = (bits << 7) | code
    while bits:
      (rows, bits) = self.encode_block(bits)
      yield rows

  def encode_string(self, message):
    return list(self.iter_encode_string(message))

  def decode_string(self, grids):
    chunks = []
    for rows in grids:
      self.decode_block(rows, chunks)
    bits = 0
    for m, digit in reversed(chunks):
      bits = bits * m + digit
    chars = []
    while bits:
      chars.append(chr(bits & 0x7f));
      bits >>= 7
    return "".join(reversed(chars))

  def encode_stream(self, fin, fout):
    message = fin.read()
    for rows in self.iter_encode_string(message):
      fout.write(format(rows) + "\n\n")

  def decode_stream(self, fin, fout):
    grids = []
    while True:
      rows = read_grid(fin)
      if not rows:
        break
      grids.append(rows)
    message = self.decode_string(grids)
    fout.write(message)

def test(coder):
  s1 = "HELLO SECRET WORLD"
  print_info("Input message:", repr(s1))
  grids = coder.encode_string(s1)
  print_info("Encoding:")
  for rows in grids:
    dump(rows)
  s2 = coder.decode_string(grids)
  print_info("Decoded message:", repr(s2))

def fail(mess):
  sys.stderr.write(mess + "\n")
  sys.exit(1)

def main():
  usage = "Usage: %prog (-e [-p] [-s] | -d | -t) [-D] < input > output"
  op = optparse.OptionParser(usage = usage)
  op.add_option("-e", "--encode", dest = "mode", action = "store_const", const = "encode",
    help = "read plain text from stdin and write sudoku grids to stdout")
  op.add_option("-d", "--decode", dest = "mode", action = "store_const", const = "decode",
    help = "read sudoku grids from stdin and write plain text to stdout")
  op.add_option("-p", "--puzzle", dest = "puzzle_mode", action = "store_true",
    help = "generate puzzle grids instead of filled-in grids")
  op.add_option("-t", "--test", dest = "mode", action = "store_const", const = "test",
    help = "run a brief internal test")
  op.add_option("-s", "--stats", dest = "stats", action = "store_true",
    help = "report encoding statistics")
  op.add_option("-D", "--debug", dest = "debug", action = "store_true",
    help = "write debugging information to stderr")
  (options, args) = op.parse_args()
  stats = Stats() if options.stats else None
  coder = Coder(options, stats)
  if options.mode == "encode":
    coder.encode_stream(sys.stdin, sys.stdout)
    if stats:
      print_info("Characters encoded: %s" % stats.chars)
      print_info("Bits encoded: %s" % stats.bits)
      print_info("Blocks used: %s" % stats.blocks)
      print_info("Entropy used: %.3f bits" % stats.entropy_used)
      print_info("Entropy unused: %.3f bits" % stats.entropy_unused)
      print_info("Clues removed by rule 1: %s" % stats.removed1)
      print_info("Clues removed by rule 2: %s" % stats.removed2)
      print_info("Clues remaining: %s" % (stats.blocks * 81 - stats.removed1 - stats.removed2))
  elif options.mode == "decode":
    coder.decode_stream(sys.stdin, sys.stdout)
  elif options.mode == "test":
    test(coder)
  else:
    fail("--encode, --decode or --test required")

if __name__ == "__main__":
  try:
    main()
  except KeyboardInterrupt:
    pass
  except (OSError, SudokuError) as e:
    fail(str(e))
