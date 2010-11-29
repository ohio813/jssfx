# -*- coding: latin1 -*-
# Copyright (c) 2006-2010 Berend-Jan "SkyLined" Wever <berendjanwever@gmail.com>
# Project homepage: http://code.google.com/p/jssfx/
# All rights reserved. See COPYRIGHT.txt for details.

HIGH_JS_CHARS =  ' ¡¢£¤¥¦§¨©ª«¬­®¯'  \
                 '°±²³´µ¶·¸¹º»¼½¾¿'  \
                 'ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏ'  \
                 'ÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞß'  \
                 'àáâãäåæçèéêëìíîï'  \
                 'ðñòóôõö÷øùúûüýþÿ';

def EncodeJavaScriptString(string):
  if string.count('"') < string.count("'"):
    quote = '"';
  else:
    quote = "'";
  result = '';
  replacements = [('\\', '\\\\'), 
                  ('\r', '\\r'), 
                  ('\n', '\\n'), 
                  (quote, '\\' + quote)];
  encoded_string = string;
  for a, b in replacements:
    encoded_string = encoded_string.replace(a, b);
  return quote + encoded_string + quote;

def FindAllIndicesForSequence(string, sequence):
  indices = [];
  last_index = 0;
  while 1:
    last_index = string.find(sequence, last_index);
    if last_index == -1:
      return indices;
    indices.append(last_index);
    last_index += len(sequence);

def GetMostRepeatedSequence(code, log_level):
  sequences = {};
  repeated_string = None;
  total_bytes = 0;
  # Find all occurances of 1 character strings:
  for i in range(len(code)):
    sequence = code[i:i + 1];
    if sequence not in sequences.keys():
      indices = FindAllIndicesForSequence(code, sequence);
      if len(indices) > 1:
        sequences[sequence] = indices;
  if log_level > 1:
    print 'Found %d characters in code' % len(sequences);
  for sequence_len in range(2, len(code) / 2):
    del_sequences = [];
    new_sequences = {};
    for sequence, indices in sequences.items():
      if len(sequence) == sequence_len - 1:
        for index in indices:
          new_sequence = code[index:index + sequence_len];
          if len(new_sequence) != sequence_len:
            # We have found something at the end of the string and cannot
            # expand it further, eg. expanding the second 'A' in '...AB...A'.
            continue;
          if new_sequence in new_sequences.keys():
            # We have already expanded this string before, eg. expanding the
            # second 'A' in 'ABxxxAB' as opposed to expanding the second 'A'
            # in '...AB...AC...'.
            continue;
          new_indices = FindAllIndicesForSequence(code, new_sequence);
          if len(new_indices) <= 1:
            # This string is not repeated, eg. expanding 'A' to 'AB' in
            # '...AB...A...'.
            continue;
          new_sequences[new_sequence] = new_indices;
          if len(new_indices) == len(indices):
            # We have expanded a string into a string that is repeated exactly
            # as often as the original. This means that we can forget about
            # the original because it is always more efficient to use the
            # longer string, eg. expanding 'A' to 'AB' in '...AB...AB...'.
            del_sequences.append(sequence);
            break;
    if len(new_sequences) == 0:
      # If there are no repeated strings of the current length, then there are
      # definitely no repeated strings of longer length, so we can stop.
      break;
    for sequence in del_sequences:
      del sequences[sequence];
    sequences.update(new_sequences);
    if log_level > 1:
      print 'Found %d sequences of %d characters in code' % \
          (len(new_sequences), sequence_len);

  best_sequence = None;
  best_total_savings = 0;
  for sequence, indices in sequences.items():
    total_savings = (len(sequence) - 1) * len(indices);
    if total_savings > best_total_savings:
      best_total_savings = total_savings;
      best_sequence = sequence;
  if log_level > 1:
    print 'Best sequences is %d characters and saves %d' % \
        (len(best_sequence), best_total_savings);
  return best_sequence;


def EncodeJavaScriptString(string):
  if string.count('"') < string.count("'"):
    quote = '"';
  else:
    quote = "'";
  result = '';
  replaces = [('\\', '\\\\'), 
              ('\r', '\\r'), 
              ('\n', '\\n'), 
              (quote, '\\' + quote)];
  encoded_string = string;
  for a, b in replaces:
    encoded_string = encoded_string.replace(a, b);
  return quote + encoded_string + quote;


def CreateResult(compressed_code, replacements):
  return 'd=%s;' % EncodeJavaScriptString(compressed_code) + \
         'for(' + \
             'c=%d;' % replacements + \
             'c--;' + \
             'd=(t=d.split(String.fromCharCode(c+%d))).join(t.pop())' % \
                 ord(HIGH_JS_CHARS[0]) + \
         ');' + \
         'eval(d)';

def JsSfx3(code, log_level):
  replacements = 0;
  compressed_code = code;
  print 'Size  | Remarks';
  print '------+'.ljust(80, '-')
  print '%5d | Original' % len(code);
  result = CreateResult(compressed_code, replacements);
  print '%5d | Initial self-extractor' % len(result);
  best_result = result;
  for char in HIGH_JS_CHARS:
    if compressed_code.find(char) != -1:
      break;
    replace_sequence = GetMostRepeatedSequence(compressed_code, log_level);
    compressed_code = compressed_code.replace(replace_sequence, char) + \
        char + replace_sequence;
    replacements += 1;
    result = CreateResult(compressed_code, replacements);
    print '%5d | Replaced %s with %s' % \
        (len(result), repr(replace_sequence), repr(char));
    if len(best_result) > len(result):
      best_result = result;
  return best_result;

if __name__ == '__main__':
  import sys;
  if len(sys.argv) != 3:
    print 'Usage: JsSfx3.py "input file" "output file"';
    sys.exit();
  try:
    input = open(sys.argv[1], 'rb').read();
  except:
    print 'Cannot read from %s' % sys.argv[1];
    sys.exit();
  output = JsSfx3(input, 1);
  try:
    open(sys.argv[2], 'wb').write(output);
  except:
    print 'Cannot write to %s' % sys.argv[2];
    sys.exit();
