# -*- coding: latin1 -*-
# Copyright (c) 2006-2010 Berend-Jan "SkyLined" Wever <berendjanwever@gmail.com>
# Project homepage: http://code.google.com/p/jssfx/
# All rights reserved. See COPYRIGHT.txt for details.
import os, sys;

VALID_JS_CHARS =  '\t'                \
                  ''                  \
                  ' !"#$%&()*+,-./'   \
                  '0123456789:;<=>?'  \
                  '@ABCDEFGHIJKLMNO'  \
                  'PQRSTUVWXYZ[\\]^_' \
                  '`abcdefghijklmno'  \
                  'pqrstuvwxyz{|}~'   \
                  ''                  \
                  ''                  \
                  ' ¡¢£¤¥¦§¨©ª«¬­®¯'  \
                  '°±²³´µ¶·¸¹º»¼½¾¿'  \
                  'ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏ'  \
                  'ÐÑÒÓÔÕÖ×ØÙÚÛÜÝÞß'  \
                  'àáâãäåæçèéêëìíîï'  \
                  'ðñòóôõö÷øùúûüýþÿ';

def PrintUsage():
  print """JsSfx - Tool for creating self-extracting compressed JavaScript.
  Copyright (c) 2006, 2010 Berend-jan "SkyLined" Wever.
  Compression algorithm replaces strings of bytes that are repeated in the
  data with shorter sequences of bytes that do not appear in the data, eg.
  'Abcdef.Abcdef.Abcdef.' could be encoded as ('X', 'XXXAbcdef.'). Output is
  a piece of JavaScript that contains the compressed data and will decompressed
  it when it is executed. Once the data is decompressed, it is executed using
  "eval()".

Usage:
  JsSfx.py input_file output_file [options]

Options:
  --strip
     Remove comments and superfluous whitespace and semi-colons from input
     JavaScript before compression.
  --strip-only
     Same as --strip, but do not compress the data.
  --log-level=number
     Specify the amount of output to show during compression. 0 = limited, 1 =
     verbose, 2 = very verbose.
  --max-unused-str-len=number
     Force using a specific decoder stub.
     Use "1" for a small decoder stub with compression limited to replacing
     sequences of bytes with unused single bytes. This works best for small
     files that do not use many different characters.
     Use "2" for s slightly larger decoder which allows for more compression.
     This works better with larger files or files that use many different bytes
     because more bytes could be saved by the additional compression than are
     added because of the larger decoder stub, making the output smaller.
     Currently, only "1" and "2" are supported, as larger unused string sizes
     are not expected to be required to encode any JavaScript file of sane size.
     by default, the program will try "1" first and if additional compression
     is possible, it will try "2" as well and choose whichever yielded the
     smallest result.""";

def Main(*argv):
  input_file_path = None;
  output_file_path = None;
  max_unused_str_len = None;
  log_level = 0;
  use_strip = False;
  strip_only = False;
  for arg in argv:
    if arg.startswith('-'):
      if arg in ['-?', '-h', '--help']:
        PrintUsage();
        return True;
      elif arg == '--strip':
        use_strip = True;
      elif arg == '--strip-only':
        use_strip = True;
        strip_only = True;
      elif arg.startswith('--max-unused-str-len='):
        max_unused_str_len = int(arg[len('--max-unused-str-len='):]);
        if max_unused_str_len not in [1, 2]:
          print 'max-unused-str-len value must be 1 or 2.';
          PrintUsage();
          return False;
      elif arg.startswith('--log-level='):
        log_level = int(arg[len('--log-level='):]);
        if log_level not in [0, 1, 2]:
          print 'log_level value must be 0, 1 or 2.';
          PrintUsage();
          return False;
      else:
        print 'Unknown switch: "%s".' % arg;
        PrintUsage();
        return False;
    elif input_file_path is None:
      input_file_path = arg;
    elif output_file_path is None:
      output_file_path = arg;
    else:
      print 'Surplus argument: "%s".' % arg;
      PrintUsage();
      return False;

  if input_file_path is None:
    print 'Missing input file argument.';
    PrintUsage();
    return False;
  elif output_file_path is None:
    print 'Missing output file argument.';
    PrintUsage();
    return False;
  
  input_file_handle = None;
  output_file_handle = None;
  try:
    try:
      input_file_handle = open(input_file_path, 'rb');
    except Exception, e:
      print 'Cannot open input file "%s".' % input_file_path;
      print repr(e);
      return False;

    input_file_content = input_file_handle.read();
    data = input_file_content;
    if use_strip:
      data = Strip(data, log_level);
    if not strip_only:
      data = TryJsSfx(data, max_unused_str_len, log_level);
    output_file_content = data;
    if len(output_file_content) > len(input_file_content):
      print 'The file cannot be compressed.';
      print 'The compressed file is %d bytes larger than the original.' % \
          (len(output_file_content) - len(input_file_content));
      return False;
    elif len(output_file_content) == len(input_file_content):
      print 'The file cannot be compressed.';
      print 'The compressed file is as large as the original.';
      return False;
    else:
      print 'The file was compressed from %d to %d bytes (%d%%).' % \
          (len(input_file_content), len(output_file_content), \
          100 * len(output_file_content) / len(input_file_content));
      try:
        output_file_handle = open(output_file_path, 'wb');
      except Exception, e:
        print 'Cannot open output file "%s".' % output_file_path;
        print repr(e);
        return False;
      output_file_handle.write(output_file_content);
      return True;
  finally:
    if input_file_handle is not None:
      input_file_handle.close();
    if output_file_handle is not None:
      output_file_handle.close();

def TryJsSfx(data, max_unused_str_len, log_level):
  js_sfxs = [];
  # If max_unused_str_len is 1 or auto, get a JsSfx object for max unused
  # string size 1:
  try1 = max_unused_str_len in [None, 1];
  try2 = max_unused_str_len == 2;
  if try1:
    print 'Adding 1 byte compressor and compressing...';
    js_sfx = JsSfx(data, 1, log_level);
    js_sfx.Compress();
    js_sfxs.append(js_sfx);
    if js_sfx.ran_out_of_unused_strs:
      try2 = max_unused_str_len is None;
      print 'Further compression might be possible.';
      if not try2:
        print '(Consider using "--max-unused-str-len=2").';
  if try2:
    print 'Adding 2 byte compressor and compressing...';
    js_sfx = JsSfx(data, 2, log_level);
    js_sfx.Compress();
    js_sfxs.append(js_sfx);
  # If we only created one JsSfx object, or the first is smaller than the
  # second, use the first JsSfx object. Otherwise use the second:
  if len(js_sfxs) == 1 or len(js_sfxs[0]) < len(js_sfxs[1]):
    if len(js_sfxs) != 1:
      print 'Using 1 byte unused strings is most efficient.';
    js_sfx = js_sfxs[0];
  else:
    if len(js_sfxs) != 1:
      print 'Using 2 byte unused strings is most efficient.';
    js_sfx = js_sfxs[1];
  return str(js_sfx);

class JsSfx(object):
  def __init__(self, compressed_str, max_unused_str_len, log_level, \
      decompress_str = '', two_char_switch_index = None):
    self.decompress_str = decompress_str;
    self.compressed_str = compressed_str;
    self.log_level = log_level;
    self.max_unused_str_len = max_unused_str_len;
    if two_char_switch_index is None:
      self.two_char_switch_index = len(decompress_str) + 1;
    else:
      self.two_char_switch_index = two_char_switch_index;
    self.ran_out_of_unused_strs = False;

  def ReplaceCompress(self, unused_str, repeated_str):
    new_decompress_str = self.decompress_str + unused_str;
    two_char_switch_index = self.two_char_switch_index;
    if len(unused_str) == 1:
      two_char_switch_index += 1;
    new_compressed_str = self.compressed_str.replace( \
        repeated_str, unused_str) + unused_str + repeated_str;
    return JsSfx(new_compressed_str, self.max_unused_str_len, self.log_level, \
        new_decompress_str, two_char_switch_index);

  def __len__(self):
    return len(str(self));

  def __str__(self):
    if self.max_unused_str_len == 1:
      return \
          'd=%s;' % EncodeJavaScriptString(self.compressed_str) + \
          'for(' + \
              'c=%d;' % len(self.decompress_str) + \
              'c--;' + \
              'd=(t=d.split(%s.charAt(c))).join(t.pop())' % \
                  EncodeJavaScriptString(self.decompress_str) + \
          ');' + \
          'eval(d)';
    elif self.max_unused_str_len == 2:
      start_index = len(self.decompress_str);
      return \
          'd=%s;' % EncodeJavaScriptString(self.compressed_str) + \
          'for(' + \
              'c=%d;' % start_index + \
              'c;' + \
              'd=(t=d.split(%s.substr(c-=(x=c<%d?1:2),x))).join(t.pop())' % \
                  (EncodeJavaScriptString(self.decompress_str), \
                      self.two_char_switch_index + 1) + \
          ');' + \
          'eval(d)';

  def GetSmallestUnusedString(self):
    if self.log_level >= 2:
      print 'Searching for smallest unused string of at most %d chars:' % \
          self.max_unused_str_len;
    seqs = [''];
    seqs_len = 0;
    while seqs_len < 2 and seqs_len < self.max_unused_str_len:
      new_seqs = [];
      for seq in seqs:
        for char in VALID_JS_CHARS:
          new_seq = seq + char;
          if self.compressed_str.find(new_seq) == -1:
            if self.log_level >= 1:
              print ('\rSmallest unused string = %s.' % \
                  repr(new_seq)).ljust(79);
            return new_seq;
          new_seqs.append(new_seq);
      seqs = new_seqs;
      seqs_len += 1;
      if self.log_level >= 2:
        print '\rSearching for smallest unused string... ' \
            '(%d chars, %d variation)' % (seqs_len, len(seqs));
    if self.log_level >= 2:
      print '\rFound no unused string.'.ljust(79);
    return None;

  def GetMostRepeatedStrings(self, min_len):
    seqs = {};
    if self.log_level >= 1:
      print 'Looking for repeated string of at least %d chars:' % min_len;
    for i in range(0, len(self.compressed_str) - min_len * 2 + 1):
      seq = self.compressed_str[i:i + min_len];
      if seq not in seqs.keys():
        indices = FindSubStrings(self.compressed_str, seq);
        if len(indices) > 1:
          seqs[seq] = indices;
    if self.log_level >= 2:
      print '- Found %d repeated strings of %d chars.' % \
          (len(seqs), min_len);
    for seq_len in range(min_len + 1, len(self.compressed_str) / 2):
      del_seqs = [];
      new_seqs = {};
      for seq, indices in seqs.items():
        if len(seq) == seq_len - 1:
          for index in indices:
            new_seq = self.compressed_str[index:index + seq_len];
            if len(new_seq) != seq_len:
              # We have found something at the end of the string and cannot
              # expand it further, eg. expanding the second 'A' in '...AB...A'.
              continue;
            if new_seq in new_seqs.keys():
              # We have already expanded this string before, eg. expanding the
              # second 'A' in 'ABxxxAB' as opposed to expanding the second 'A'
              # in '...AB...AC...'.
              continue;
            new_indices = FindSubStrings(self.compressed_str, new_seq);
            if len(new_indices) <= 1:
              # This string is not repeated, eg. expanding 'A' to 'AB' in
              # '...AB...A...'.
              continue;
            new_seqs[new_seq] = new_indices;
            if len(new_indices) == len(indices):
              # We have expanded a string into a string that is repeated exactly
              # as often as the original. This means that we can forget about
              # the original because it is always more efficient to use the
              # longer string, eg. expanding 'A' to 'AB' in '...AB...AB...'.
              del_seqs.append(seq);
              break;
      if len(new_seqs) == 0:
        # If there are no repeated strings of the current length, then there are
        # definitely no repeated strings of longer length, so we can stop.
        if self.log_level >= 2:
          print 'Found no repeated strings of %d chars.   ' % seq_len;
        break;
      for seq in del_seqs:
        del seqs[seq];
      seqs.update(new_seqs);
      if len(del_seqs) > 0:
        if self.log_level >= 2:
          print '- Expanded %d repeated strings of %d chars to %d chars.' % \
              (len(del_seqs), seq_len - 1, seq_len);
      if len(new_seqs) - len(del_seqs) > 0:
        if self.log_level >= 2:
          print '- Found %d repeated strings of %d chars.' % \
              (len(new_seqs) - len(del_seqs), seq_len);
      print '\rFound %d repeated strings.' % len(seqs),;
    return seqs;

  def Compress(self):
    while 1:
      unused_string = self.GetSmallestUnusedString();
      if unused_string is None:
        self.ran_out_of_unused_strs = True;
        print 'No more unused strings available for replacing.';
        break;
      seqs = self.GetMostRepeatedStrings(len(unused_string) + 1);
      if len(seqs) == 0:
        print 'No more repeated strings available for replacing.';
        break;
      if self.log_level >= 1:
        print 'Looking for best compression among %d possible replacements:' % \
            len(seqs);
      best_saved_bytes = 0;
      best_new_js_sfx = None;
      progress = 0;
      last_percent = -1;
      for seq, indices in seqs.items():
        progress += 1;
        new_js_sfx = self.ReplaceCompress(unused_string, seq);
        saved_bytes = len(self) - len(new_js_sfx);
        if saved_bytes > best_saved_bytes:
          best_saved_bytes = saved_bytes;
          best_new_js_sfx = new_js_sfx;
          if self.log_level >= 1:
            print '\r- Replacing %d * %s with %s will save %d bytes.' % \
                (len(indices), repr(seq), repr(unused_string), saved_bytes);
          last_percent = -1;
        percent = 100 * progress / len(seqs);
        if percent > last_percent:
          print '\rChecking replace %d/%d (%d%%)...' % \
              (progress, len(seqs), percent),;
          last_percent = percent;
      if best_new_js_sfx is None:
        print '\rAvailable repeated and unused strings do not allow further ' \
            'compression.'.ljust(79);
        break;
      else:
        print '\rReplace reduced size from %d to %d bytes' % \
            (len(self), len(best_new_js_sfx));
        self.decompress_str = best_new_js_sfx.decompress_str;
        self.compressed_str = best_new_js_sfx.compressed_str;
        self.max_unused_str_len = best_new_js_sfx.max_unused_str_len;
        self.two_char_switch_index = best_new_js_sfx.two_char_switch_index;

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


def FindSubStrings(string, substr):
  indices = [];
  index = 0;
  while 1:
    index = string.find(substr, index);
    if index == -1:
      return indices;
    indices.append(index);
    index += 1;

CHARS_REQUIRING_SEPARATION = \
    '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_';

def Strip(in_data, log_level):
  out_data = Stripper(in_data, log_level).GetStrippedData();
  print 'The file was stripped from %d to %d bytes (%d%%).' % \
      (len(in_data), len(out_data), 100 * len(out_data) / len(in_data));
  return out_data;

class Stripper(object):
  def __init__(self, in_data, log_level):
    self.in_data = in_data;
    self.log_level = log_level;
    self.index = 0;
    self.out_data = '';

    self.whitespace_strip_map = {
        '//': self.StripLineComment,
        '/*': self.StripBlockComment,
    };
    self.strip_map = {
        '//': self.StripLineComment,
        '/*': self.StripBlockComment,
        '\'': self.StripQuotedString,
        '"':  self.StripQuotedString,
        '\r': self.StripUnneededWhiteSpace,
        '\n': self.StripUnneededWhiteSpace,
        ' ':  self.StripUnneededWhiteSpace,
        '\t': self.StripUnneededWhiteSpace,
    };

  def GetStrippedData(self):
    non_stripped = '';
    while self.index < len(self.in_data):
      for header, handler in self.strip_map.items():
        if self.in_data[self.index:self.index + len(header)] == header:
          if len(non_stripped) > 0:
            if self.log_level == 2: print '+data   : %s' % repr(non_stripped);
            self.out_data += non_stripped;
            non_stripped = '';
          handler();
          break;
      else:
        non_stripped += self.in_data[self.index];
        self.index += 1;
    if self.log_level == 2: print '+data   : %s' % repr(non_stripped);
    self.out_data += non_stripped;
    return self.out_data.replace(';;', ';').replace(';}', '}');

  def StripLineComment(self):
    # Starts with //, so skip first 2 chars
    comment = self.in_data[self.index:self.index + 2];
    self.index += 2; 
    while self.index < len(self.in_data):
      char = self.in_data[self.index];
      if char in '\r\n':
        break;
      comment += char;
      self.index += 1;
    if self.log_level == 2: print '-comment: %s' % repr(comment);
  
  def StripBlockComment(self):
    # Starts with /*, so skip first 2 chars
    comment = self.in_data[self.index:self.index + 2];
    self.index += 2; 
    while self.index < len(self.in_data): 
      char = self.in_data[self.index];
      comment += char;
      if char == '*' and self.in_data[self.index + 1] == '/':
        comment += '/';
        break;
      self.index += 1;
    else:
      raise AssertionError('Unterminated block comment found.');
    if self.log_level == 2: print '-comment: %s' % repr(comment);
  
  def StripQuotedString(self):
    # Starts with quote, so skip first char
    quote = string = self.in_data[self.index];
    self.index += 1; 
    escaped = False;
    while self.index < len(self.in_data):
      char = self.in_data[self.index];
      string += char;
      self.index += 1; 
      if not escaped and char == quote:
        self.out_data += string;
        break;
      escaped = char == '\\';
    else:
      raise AssertionError('Unterminated quoted string found.');
    if self.log_level == 2: print '+string : %s' % repr(string);

  def StripUnneededWhiteSpace(self):
    # Starts with whitespace, so skip first char:
    in_whitespace = self.in_data[self.index];
    out_whitespace = '';
    self.index += 1; 
    while self.index < len(self.in_data): 
      for header, handler in self.whitespace_strip_map.items():
        if self.in_data[self.index:self.index + len(header)] == header:
          handler();
          break;
      else:
        char = self.in_data[self.index];
        if char in ' \t\r\n':
          in_whitespace += char;
          self.index += 1; 
        else:
          if len(self.out_data) == 0:
            msg = 'whitespace at start of data';
          elif char in CHARS_REQUIRING_SEPARATION \
              and self.out_data[-1] in CHARS_REQUIRING_SEPARATION:
            msg = 'combining %s and %s requires whitespace' % (repr(self.out_data[-1]), repr(char));
            out_whitespace = ' ';
          else:
            msg = 'combining %s and %s does not require whitespace' % (repr(self.out_data[-1]), repr(char));
          break;
    else:
      msg = 'whitespace until end of data';
    self.out_data += out_whitespace;
    if in_whitespace == out_whitespace:
      if self.log_level == 2: print '+spacing: %s (%s)' % (repr(out_whitespace), msg);
    elif out_whitespace == '':
      if self.log_level == 2: print '-spacing: %s (%s)' % (repr(in_whitespace), msg);
    else:
      if self.log_level == 2: print '~spacing: %s => %s (%s)' % (repr(in_whitespace), repr(out_whitespace), msg);

if __name__ == "__main__":
  success = Main(*sys.argv[1:]);
  if not success:
    sys.exit(-1);