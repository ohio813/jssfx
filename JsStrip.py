# Copyright (c) 2006-2010 Berend-Jan "SkyLined" Wever <berendjanwever@gmail.com>
# Project homepage: http://code.google.com/p/jssfx/
# All rights reserved. See COPYRIGHT.txt for details.

# TODO: this list does not include high ascii characters but it should!
CHARS_REQUIRING_SEPARATORS = \
    '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_';

def JsStrip(in_data, log_level):
  out_data = Stripper(in_data, log_level).GetStrippedData();
  if out_data != in_data:
    print '%5d | Stripped comments and superfluous separators' % \
        len(out_data);
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
        '\\\r\n': self.StripUnneededWhiteSpace,
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
    if len(non_stripped) > 0:
      if self.log_level == 2: print '+data   : %s' % repr(non_stripped);
      self.out_data += non_stripped;
    out_data = self.out_data.replace(';;', ';').replace(';}', '}');
    while out_data[-1] == ';':
      out_data = out_data[:-1];
    if out_data != self.out_data:
      if self.log_level == 2: print '-semi-colons (%d)' % \
        (len(self.out_data) - len(out_data));
      self.out_data = out_data;
    return self.out_data;

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
      if not escaped and self.index < len(self.in_data) - 1 and \
          self.in_data[self.index] == '\\' and self.in_data[self.index + 1] in '\r\n':
        if self.index < len(self.in_data) - 2 and self.in_data[self.index+1:self.index+3] == '\r\n':
          self.index += 3;
        else:
          self.index += 2;
      else:
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
          elif char in CHARS_REQUIRING_SEPARATORS \
              and self.out_data[-1] in CHARS_REQUIRING_SEPARATORS:
            msg = 'combining %s and %s requires whitespace' % \
                (repr(self.out_data[-1]), repr(char));
            out_whitespace = ' ';
          else:
            msg = 'combining %s and %s does not require whitespace' % \
                (repr(self.out_data[-1]), repr(char));
          break;
    else:
      msg = 'whitespace until end of data';
    self.out_data += out_whitespace;
    if in_whitespace == out_whitespace:
      if self.log_level == 2: print '+spacing: %s (%s)' % \
          (repr(out_whitespace), msg);
    elif out_whitespace == '':
      if self.log_level == 2: print '-spacing: %s (%s)' % \
          (repr(in_whitespace), msg);
    else:
      if self.log_level == 2: print '~spacing: %s => %s (%s)' % \
          (repr(in_whitespace), repr(out_whitespace), msg);

if __name__ == '__main__':
  import sys;
  if len(sys.argv) != 3:
    print 'Usage: Strip.py "input file" "output file"';
    sys.exit();
  try:
    input = open(sys.argv[1], 'rb').read();
  except:
    print 'Cannot read from %s' % sys.argv[1];
    sys.exit();
  output = Strip(input, 1);
  try:
    open(sys.argv[2], 'wb').write(output);
  except:
    print 'Cannot write to %s' % sys.argv[2];
    sys.exit();
