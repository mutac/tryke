"""
Defines class used by the rest of 
the module to inspect the torrent

TODO: Allow a torrent to be constructed
without having all the necessary data...

Copyright (C) 2007 Matt Waddell
ALL RIGHTS RESERVED
"""

import os, sha, copy
import bencode

class Torrent:
    """
    Provides a common interface to a torrent
    (not including State information)

    Data Members:

    All strings are UTF-8, the optional members may be empty

    torrent             : Torrent file
    tracker             : Tracker URL
    backupTrackers      : List of backup tracker urls (optional)
    creationDate        : Creation date (seconds since epoc) (optional)
    comment             : Creator comment (optional)
    createdBy           : Creator string (optional)

    pieceLen            : File block len (bytes)
    pieces              : List of SHA-1 hashes for all pieces
    private             : Whether the torrent is private
    fileMode            : 'single-file' or 'multi-file'
    length              : Length of entire download

    If in 'single-file' mode:
    fileName            : Name of the download file
    md5Sum              : Optional md5sum of download

    If in 'multi-file' mode:
    fileName            : Name of containing directory
    files               : List of dictionaries that describe
                          all of the files in the download:

                          file['length'] : Length of file
                          file['md5sum'] : Optional md5sum of file
                          file['path']   : Path relative to fileName
                          file['pieces'] : List of piece hashes of file

    hash                : A sha1 hash of the torrent
    """

    def __init__(self, t):
        """
        If the argument is a string, it is assumed
        to be a path to a torrent file.  If it is
        a dictionary, that is used to create the 
        torrent class instead.

        An exception will be thrown if the resulting
        dictionary is malformed.
        """

        if isinstance(t, dict):
            self.torrent = ''
            self.torrentDict = t
        elif isinstance(t, str):
            # parse the torrent
            self.torrent = t
            self.torrentDict = bencode.decodeFile(t)
        else:
            raise Exception, 'Argument must be either a Dictionary or String'

        # Top level keys:
        #

        self.tracker = self.torrentDict['announce']

        # Extension to the original spec:
        # a list of alternate trackers
        if 'announce-list' in self.torrentDict:
            self.backupTrackers = self.torrentDict['announce-list']
        else:
            self.backupTrackers = []

        if 'creation date' in self.torrentDict:
            if not isinstance(self.torrentDict['creation date'], long):
                raise Exception, 'Creation date is malformed'
            self.creationDate = int(self.torrentDict['creation date'])
        else:
            self.creationDate = 0

        if 'comment' in self.torrentDict:
            self.comment = self.torrentDict['comment']
        else:
            self.comment = ''

        if 'created by' in self.torrentDict:
            self.createdBy = self.torrentDict['created by']
        else:
            self.createdBy = ''

        # Info Dictionary
        #

        info = self.torrentDict['info']

        # The tracker identifies the torrent
        # by a hash of the bencoded info dict
        infoStr = bencode.encode(info)
        s = sha.new(infoStr)
        self.hash = s.digest()

        self.pieceLen = info['piece length']

        # Parse the peices list:
        # Input consists of one long string of
        # 20 byte sha1 hashes.  break them up
        # and produce a list of hashes.

        lenPieces = len(info['pieces'])
        hashLen = 20
        if lenPieces % hashLen != 0:
            raise Exception, 'List of file hashes is incomplete'

        self.pieces = []
        i,j = 0, hashLen
        while j < lenPieces:
            p = info['pieces'][i:j]
            self.pieces.append(p)
            i += hashLen
            j += hashLen 

        if 'private' in info:
            if not isinstance(info['private'], long):
                raise Exception, 'Private bit is malformed'
            self.private = bool(info['private'])
        else:
            self.private = False

        # Advisory file/directory name for the download
        self.fileName = info['name']

        self.files = []
        # Determine mode (multi-file, or single-file)
        if 'files' in info:
            # if its a multi-file torrent
            # it will have a list of files
            # along with their lengths,
            # path/filenames, and optionally
            # and md5sums.
            self.fileMode = 'multi-file'

            self.files = []
            totalLen = 0
            pieceIndex = 0
            for file in info['files']:

                # Fix up the file dict
                # 

                f = {}
                if not isinstance(file['length'], long):
                    raise Exception, 'File length is malformed'

                f['length'] = file['length']
                totalLen += f['length']
                
                if 'md5sum' in file:
                    f['md5sum'] = file['md5sum']
                else:
                    f['md5sum'] = ''

                # The torrent stores the path as a list
                # of path components...
                # Join them together into a usable path
                # relative to the base dir--self.file
                f['path'] = os.sep.join(file['path'])

                # Get list of piece hashes
                #
                numPieces,mod = divmod(f['length'],self.pieceLen)
                
                # Round up to the next piece
                if mod:
                    numPieces += 1

                f['pieces'] = self.pieces[pieceIndex : pieceIndex + numPieces]
                pieceIndex += numPieces

                self.files.append(f)

            # Total length of the download
            self.length = totalLen

        else:
            # if its just a single file torrent 
            # it may have a single md5sum.
            self.fileMode = 'single-file'

            # Total length of the download
            self.length = info['length']

            if 'md5sum' in info:
                self.md5sum = info['md5sum']
            else:
                self.md5sum = ''

    def toDict(self):
        """
        Converts the torrent class back to a
        dictionary.
        """
        pass
    
    def toString(self):
        """
        Converts torrent back to a bencoded
        string.
        """
        pass
