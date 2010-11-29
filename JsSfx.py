# Copyright (c) 2006-2010 Berend-Jan "SkyLined" Wever <berendjanwever@gmail.com>
# Project homepage: http://code.google.com/p/jssfx/
# All rights reserved. See COPYRIGHT.txt for details.
import os, sys;

from JsSfx12 import JsSfx12;
from JsSfx3 import JsSfx3;
from Strip import Strip;

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
  print 'Trying JsSfx3...';
  js_sfxs.append(JsSfx3(data, log_level));
  if try1:
    print 'Adding 1 byte compressor and compressing...';
    js_sfx = JsSfx12(data, 1, log_level);
    js_sfx.Compress();
    js_sfxs.append(js_sfx);
    if js_sfx.ran_out_of_unused_strs:
      try2 = max_unused_str_len is None;
      print 'Further compression might be possible.';
      if not try2:
        print '(Consider using "--max-unused-str-len=2").';
  if try2:
    print 'Adding 2 byte compressor and compressing...';
    js_sfx = JsSfx12(data, 2, log_level);
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

if __name__ == "__main__":
  success = Main(*sys.argv[1:]);
  if not success:
    sys.exit(-1);