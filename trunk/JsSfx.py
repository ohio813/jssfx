# -*- coding: latin1 -*-
# Copyright (c) 2006-2010 Berend-Jan "SkyLined" Wever <berendjanwever@gmail.com>
# Project homepage: http://code.google.com/p/jssfx/
# All rights reserved. See COPYRIGHT.txt for details.
import os, sys;

from Strip import Strip;
from JsSfx12 import JsSfx12;
from JsSfx32 import JsSfx32;

ASCII_JS_CHARS =  '\1\2\3\4\5\6\7\b\t\r\x0b\f\n\x0e\x0f' \
                  '\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f' \
                  ' !"#$%&\'()*+,-./' \
                  '0123456789:;<=>?'  \
                  '@ABCDEFGHIJKLMNO'  \
                  'PQRSTUVWXYZ[\\]^_' \
                  '`abcdefghijklmno'  \
                  'pqrstuvwxyz{|}~\x7f';
LATIN1_JS_CHARS = ASCII_JS_CHARS +    \
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
  JsSfx removes comments and superfluous separation characters (whitespace and
  semi-colons) from an input JavaScript and applies various compression
  techniques with various settings to it. It outputs the smallest self-
  extracting compressed version of the script that it created.

Usage:
  JsSfx.py input_file output_file [options]

Options:
  --no-strip
     Do not remove comments and superfluous separation characters from the input
     JavaScript before compression.
  --no-compress
     Do not try to compress the script.
  --ascii
     Use only ASCII characters (00-7F) rather than latin-1 (00-7F+A0-FF).
  --log-level=number
     Specify the amount of output to show during compression. 0 = limited, 1 =
     verbose, 2 = very verbose.
  --exhaustive
     By default, not all possible ways to use all available characters during
     compression are applied (to speed up the compression process). Use this
     option to have the code try them all and find the best one. This may
     slightly increase compression in some cases, but requires a lot more time
     to process the script.
""";

def Main(*argv):
  input_file_path = None;
  output_file_path = None;
  log_level = 0;
  use_ascii = False;
  use_strip = True;
  use_compress = True;
  quick_and_dirty = True;
  for arg in argv:
    if arg.startswith('-'):
      if arg in ['-?', '-h', '--help']:
        PrintUsage();
        return True;
      elif arg == '--no-strip':
        use_strip = False;
      elif arg == '--no-compress':
        use_compress = False;
      elif arg == '--ascii':
        use_ascii = True;
      elif arg == '--exhaustive':
        quick_and_dirty = False;
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
    print;
    print ''.ljust(80, '=');
    print ' JsSfx - JavaScript self-extracting compressed script generator.';
    print ' Copyright (c) 2006-2010 Berend-Jan "SkyLined" Wever <berendjanwever@gmail.com>';
    print ' Project homepage: http://code.google.com/p/jssfx/';
    print ''.ljust(80, '=');
    print;
    print ' Size   Remarks';
    print '======v'.ljust(80, '=');
    print '%5d | Original size' % len(data);
    if use_strip:
      data = Strip(data, log_level);
    if use_compress:
      if use_ascii:
        valid_chars = ASCII_JS_CHARS;
        valid_chars_description = 'ASCII';
      else:
        valid_chars = LATIN1_JS_CHARS;
        valid_chars_description = 'latin1';
      compressed = [];
      # Try v1.1
      js_sfx = JsSfx12(data, valid_chars, valid_chars_description, 1, log_level);
      js_sfx.Compress();
      compressed.append(str(js_sfx));
      if js_sfx.ran_out_of_unused_strs:
        # Try v1.2
        js_sfx = JsSfx12(data, valid_chars, valid_chars_description, 2, log_level);
        js_sfx.Compress();
        compressed.append(str(js_sfx));
      # Try v3.1/3.2
      compressed.append(JsSfx32(data, valid_chars, valid_chars_description, log_level, quick_and_dirty));
      valid_non_slash_chars = valid_chars;
      data = compressed[0];
      # Select whatever yielded the shortest result.
      for i in range(1, len(compressed)):
        if len(compressed[i]) < data:
          data = compressed[i];
    output_file_content = data;
    print '======^'.ljust(80, '=');
    print;
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

if __name__ == "__main__":
  success = Main(*sys.argv[1:]);
  if not success:
    sys.exit(-1);