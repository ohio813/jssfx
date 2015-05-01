JsSfx removes comments and superfluous separation characters (whitespace and
semi-colons) from an input JavaScript and applies various compression
techniques with various settings to it. It outputs the smallest self-
extracting compressed version of the script that it created.

Usage:
> JsSfx.py input\_file output\_file [options](options.md)

Options:
> --no-strip
> > Do not remove comments and superfluous separation characters from the input
> > JavaScript before compression.

> --no-compress
> > Do not try to compress the script.

> --ascii
> > Use only ASCII characters (00-7F) rather than latin-1 (00-7F+A0-FF).

> --log-level=number
> > Specify the amount of output to show during compression. 0 = limited, 1 =
> > verbose, 2 = very verbose.

> --exhaustive
> > By default, not all possible ways to use all available characters during
> > compression are applied (to speed up the compression process). Use this
> > option to have the code try them all and find the best one. This may
> > slightly increase compression in some cases, but requires a lot more time
> > to process the script.

Requirements:

> - Python 2.