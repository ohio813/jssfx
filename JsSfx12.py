# -*- coding: latin1 -*-
# Copyright (c) 2006-2010 Berend-Jan "SkyLined" Wever <berendjanwever@gmail.com>
# Project homepage: http://code.google.com/p/jssfx/
# All rights reserved. See COPYRIGHT.txt for details.

JS_CHARS =        '\t'                \
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

def FindSubStrings(string, substr):
  indices = [];
  index = 0;
  while 1:
    index = string.find(substr, index);
    if index == -1:
      return indices;
    indices.append(index);
    index += len(substr);

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

class JsSfx12(object):
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
    return JsSfx12(new_compressed_str, self.max_unused_str_len, self.log_level, \
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
        for char in JS_CHARS:
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

