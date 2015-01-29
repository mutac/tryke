"""
Defines the necessary parsers for the BT protocol,
including those necessary for the meta files i.e. Torrent files.

Copyright (C) 2007 Matt Waddell
ALL RIGHTS RESERVED
"""

import string

symbols = {}
symbols['dict'] = 'd'
symbols['list'] = 'l'
symbols['int'] = 'i'
symbols['end'] = 'e'
symbols['strLenSep'] = ':'

def encode(struct):
    """
    Given a structure, encode
    it using bencoding

    Supported data structures:
        Dictionary
        List
        Integer (Long)
        String

    Lists and Dictionaries may be nested

    See:
    http://wiki.theory.org/BitTorrentSpecification#bencoding
    """

    def __encode(struct):
        """
        Recursively construct a bencoded
        string from a structure.
        """

        if isinstance(struct, dict):
            s = symbols['dict']

            # Apprently the keys have to be sorted
            # lexicographically
            keys = struct.keys()
            keys.sort()
            for key in keys:
                # Keys must be strings as well
                if not isinstance(key, str):
                    raise Exception, 'Dictionary keys must be Strings'

                val = struct[key]
                keyEnc = __encode(key)
                valEnc = __encode(val)
                s += '%s%s' % (keyEnc,valEnc)
            s += symbols['end']
            return s
        elif isinstance(struct, list):
            s = symbols['list']
            for val in struct:
                s += __encode(val)
            s += symbols['end']
            return s
        elif isinstance(struct, int) or isinstance(struct, long):
            return '%s%d%s' % (symbols['int'],struct,symbols['end'])
        elif isinstance(struct, str):
            return '%d%s%s' % (len(struct), symbols['strLenSep'], struct)
        else:
            raise Exception, 'Unsupported structure: %s' % struct.__class__.__name__

    try:
        s = __encode(struct)
    except Exception, msg:
        raise 'Encode Error: %s' % str(msg)

    return s

def decode(s, strict = False):
    """
    Parses a bencoded stream
    returning the appropriate 
    data structures.

    Strict:
        If `strict` is True, the parser will halt if:
        
        Dictionary keys are not strings
        Dictionary keys do not appear in sorted order

    See:
    http://wiki.theory.org/BitTorrentSpecification#bencoding
    """

    def __decode(parts):
        """
        Recursive descent parser:
        Works backwards on a list
        of characters, and returns
        the next whole part of a
        bencoded string.  
        """

        c = parts.pop()

        if c == symbols['dict']:
            # Parse Dictionary
            # i.e. d3:fooi123ee

            c = parts.pop()
            d = {}
            inputOrderedKeys = []
            while c != symbols['end']:
                parts.append(c)
                key = __decode(parts)
                
                # Save the input order of the key if
                # using strict evaluation
                if strict:
                    inputOrderedKeys.append(key)

                # Specification states that the dict keys
                # must be strings
                if strict and not isinstance(key, str):
                    raise Exception, 'Dictionary keys must be Strings'

                d[key] = __decode(parts)
                if not parts:
                    raise Exception, 'Unexpected EOF in Dict declaration'
                c = parts.pop()

            # Check that the keys were in sorted order
            # if using strict evaluation
            if strict:
                sortedKeys = d.keys()
                sortedKeys.sort()
                if sortedKeys != inputOrderedKeys:
                    raise Exception, 'Dictionary keys must be in sorted order'

            return d
        elif c == symbols['list']:
            # Parse List
            # i.e. l3:foo3:bare

            c = parts.pop()
            l = []
            while c != symbols['end']:
                parts.append(c)
                val = __decode(parts)
                l.append(val)
                if not parts:
                    raise Exception, 'Unexpected EOF in List declaration'
                c = parts.pop()
            return l
        elif c == symbols['int']:
            # Parse Integer
            # i.e. i345e

            c = parts.pop()
            num = ''
            while c != symbols['end']:
                num += c
                if not parts:
                    raise Exception, 'Unexpected EOF in Integer declaration'
                c = parts.pop()

            try:
                num = long(num)
            except:
                raise Exception, 'Malformed Integer value: %s' % num 

            return num
        elif c in string.digits:
            # Parse string  
            # i.e. 5:hello

            # Parse string length
            num = c
            c = parts.pop()
            while c != symbols['strLenSep']:
                num += c
                if not parts:
                    raise Exception, 'Unexpected EOF in String declaration'
                c = parts.pop()

            try:
                num = int(num)
            except:
                raise (Exception,
                    'Malformed Integer value in String length: %s' % num)

            # Now read num characters
            s = ''
            while num > 0:
                if not parts:
                    raise Exception, 'Unexpected EOF in String declaration'
                c = parts.pop()
                s += c
                num -= 1
            return s

        else:
            raise Exception, 'Unexpected Character: %s' % c

    chars = list(s)
    chars.reverse()
    try:
        tree = __decode(chars)
    except Exception, msg:
        raise Exception, 'Parse Error: ' + str(msg)
    return tree

def decodeFile(torrentFile, strict = False):
    """
    Parses a file file, and returns
    a dictionary containing its values
    """

    try:
        fd = open(torrentFile)
    except:
        raise Exception, 'Unable to open torrent file: %s' % torrentFile

    s = fd.read()
    return decode(s, strict)

def __test(torrentFile):
    """
    Tests to see if the encoder/decoder work correctly
    """

    t1 = decodeFile(torrentFile, True)
    s1 = encode(t1)
    t2 = decode(s1, True)
    s2 = encode(t2)

    return (t1 == t2) and (s1 == s2)
