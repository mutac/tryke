"""
Defines a nice interface to interact
with a torrent.

Copyright (C) 2007 Matt Waddell
ALL RIGHTS RESERVED
"""

import torrent, state
import random, string

clientPrefix = 'PY'
clientVersion = '0001'

class Client:
    """
    Provides easy access to the high level
    functions of a torrent.
    """

    def __init__(self, tor, port, ip = None):

        tor = torrent.Torrent(tor)

        # Port to listen for connection on
        self.port = port

        # Optional external IP address
        self.ip = ip

        # Generate a peer ID
        self.peerID = newPeerID()

        # Initial state of the torrent
        self.state = state.State(tor, self.peerID, self.port, self.ip)

        self.numPeers = 25

    def start(self):
        """
        Starts the torrent
        """

        self.state.start(self.numPeers)

    def stop(self):
        """
        Stops the torrent
        """

        self.state.stop()

    def setUserAgent(self, userAgent):
        """
        Sets the user agent string, used
        when contacting the tracker.
        """
        self.state.setUserAgent(userAgent)

    def setPeerID(self, peerID):
        """
        Sets the peer id here and in the
        state where it is actually used.
        """
        self.peerID = peerID
        self.state.setPeerID(peerID)

    def setNewPeerID(self, prefix = clientPrefix, ver = clientVersion):
        """
        Creates and sets a new peer id
        """
        peerID = newPeerID(prefix, ver)
        self.setPeerID(peerID)

    def emulate(self, cli):
        """
        Makes the client emulate a particular 
        main-stream bt client.

        Doesn't fully emulate the nuances though...
        only sends the appropriate peer_id and
        user-agent strings.
        """

        peerID,userAgent = emulateClient(cli)
        self.setPeerID(peerID)
        self.setUserAgent(userAgent)

################

def emulateClient(cli):
    """
    Makes the client emulate a particular 
    main-stream bt client.

    Doesn't fully emulate the nuances though...
    only sends the appropriate peer_id and
    user-agent strings.

    cli:
        'azureus'
        'utorrent'
    """
    cli = cli.lower()

    peerID = ''
    userAgent = ''

    # Update as the versions change
    if cli == 'azureus':
        peerID = newPeerID('AZ', '2504')
        userAgent = 'Azureus 2.5.0.4;Linux;Java 1.5.0_10'
    elif cli == 'utorrent':
        peerID = newPeerID('UT', '1720')
        userAgent = 'uTorrent/1720'
    else:
        raise Exception, 'Unrecognized client string'

    return (peerID,userAgent)

def newPeerID(prefix = clientPrefix, ver = clientVersion):
    """
    Returns a new 20 byte Peer ID.

    Form: 
    '-', 2 char prefix, 4 char version, random, '-'

    `prefix' may be set to emulate other clients
    """

    if len(prefix) > 2:
        prefix = prefix[0:2]

    if len(ver) > 4:
        ver = ver[0:4]

    random.seed()
    # Produce 17 random digits
    digits = ''
    for i in xrange(20 - (len(prefix) + len(ver) + 2) ):
        digits += random.choice(string.digits + string.letters)

    return '-%s%s-%s' % (prefix,ver,digits)
