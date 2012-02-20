import base64, math, struct, zlib;

from Png import *;

class JsPng(object):
  def __init__(self, code, use_png_html, use_ascii, log_whatever, log_level):
    self.code = code;
    self.use_png_html = use_png_html;

  def __str__(self):
    if self.use_png_html:
      return str(HtmlPng(self.code));
    else:
      return str(Png(self.code));
