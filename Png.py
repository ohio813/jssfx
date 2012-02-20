import base64, math, struct, zlib;

SCRIPT_GET_IMAGE_DATA = \
    'd=c.getContext(\'2d\');' + \
    'd.drawImage(this,0,0);' + \
    'e=d.getImageData(0,0,n=%(length)d,1).data;';

SCRIPT_DECODE_GS_DATA =  \
    'for(' + \
      's=\'\';' + \
      'n--;' + \
      's+=String.fromCharCode(e[n*4])' + \
    ');';

SCRIPT_EXECUTE_DECODE_DATA = \
    'eval(s);';

HTML = '<canvas id=c height=1 width=%(length)d></canvas><img src=%(src)s onload="%(script)s">';

GIF_IMAGE_BLOCK_ID = 0x2C;
GIF_TRAILER_BLOCK_ID = 0x3B;

class Png(object):
  def __init__(self, code):
    self.code = code;
    self.sub_filter = False;

  def Header(self):
    return '\x89PNG\r\n\x1a\n';

  def Chunk(self, type, data):
    assert len(type) == 4, '"type" must be a 4 byte string.';
    return  struct.pack('>L', len(data)) + \
            type + \
            data + \
            struct.pack('>l', zlib.crc32(type + data));

  def DataIHDR(self):
    return struct.pack('>LLBBBBB',
        len(self.code),     # width
        1,                  # height
        8,                  # bitdepth = 8 bits per color
        0,                  # colortype = greyscale
        0,                  # compression = inflate (32K sliding window)
        0,                  # filter = adaptive filtering with five basic filter types
        0,                  # interlace = no
    );

  def DataIDAT(self):
    reversed_code = list(self.code);
    reversed_code.reverse();
    reversed_code = ''.join(reversed_code);
    bpp = 1;
    reversed_sub_code = '';
    for x in range(len(reversed_code)):
      byte = ord(reversed_code[x]);
      if x - bpp >= 0:
        byte = (byte + 0x100 - ord(reversed_code[x - bpp])) % 0x100;
      reversed_sub_code += chr(byte);
    
    idat_unfiltered = zlib.compress('\0' + reversed_code, 9);
    idat_sub_filtered = zlib.compress('\1' + reversed_sub_code, 9);
    if len(idat_unfiltered) < len(idat_sub_filtered):
      return idat_unfiltered;
    self.sub_filter = True;
    return idat_sub_filtered;

  def DataIEND(self):
    return '';

  def __str__(self):
    return  self.Header() + \
            self.Chunk('IHDR', self.DataIHDR()) + \
            self.Chunk('IDAT', self.DataIDAT()) + \
            self.Chunk('IEND', self.DataIEND());

class Gif(object):
  def __init__(self, code):
    self.code = code;

  def Header(self):
    return 'GIF89a';

  def ScreenDescriptor(self):
    bitfield = (
        0           << 7 +    # 1 Global color table = false
        7           << 4 +    # 3 ColorResolution (not relevant)
        0           << 3 +    # 1 Sort (ignored)
        0           << 0 )    # 3 Size of global color table (ignored)
    return struct.pack('>HHBBB',
        len(self.code),       # Width
        1,                    # Height
        bitfield,             # Flags
        0,                    # Background color index (ignored)
        0);                   # Pixel aspect ratio (not relevant)

  def BlockImageData(self):
    raise NotImplementedError();
#    lzw_minimum_code_size =
#    image_data =
    return struct.pack('>B', lzw_minimum_code_size) + image_data;

  def BlockImageDescriptor(self):
    bitfield = (
        0           << 7 +    # 1 Local color table = false
        0           << 6 +    # 1 Interlace (not relevant)
        0           << 5 +    # 1 Sort (ignored)
        0           << 3 +    # 2 Reserved
        0           << 0 )    # 3 Size of local color table (ignored)
    return struct.pack('>BHHHHB', 
        GIF_TRAILER_BLOCK_ID, # Image descriptor block identifier
        0,                    # Left position
        0,                    # Top position
        len(self.code),       # Width
        1,                    # Height
        bitfield);            # Flags

  def BlockTrailer(self):
    return struct.pack('>B', 
        GIF_TRAILER_BLOCK_ID); # Trailer block identifier

  def __str__(self):
    return  self.Header() + \
            self.ScreenDescriptor() + \
            self.BlockImageDescriptor() + \
            self.BlockImageData() + \
            self.TrailerBlock();

class HtmlPng(object):
  def __init__(self, code):
    self.code = code;
    self.png = Png(code);

  def __str__(self):
    script = (
        SCRIPT_GET_IMAGE_DATA + 
        SCRIPT_DECODE_GS_DATA + 
        SCRIPT_EXECUTE_DECODE_DATA
    ) % {
      'length': len(self.code)
    };
    return HTML % {
        'src': 'data:image/png;base64,%s' % base64.b64encode(str(self.png)),
        'length': len(self.code),
        'script': script,
    };

if __name__ == "__main__":
  open('test.png.html', 'wb').write(str(HtmlPng('document.write("Hello, world!");')));