"""
Defines class used by the rest of 
the module to track the state of
a torrent client.

Copyright (C) 2007 Matt Waddell
ALL RIGHTS RESERVED
"""

import torrent, tracker

ST_NONE = 0
ST_READY = 1
ST_QUEUE = 2
ST_SCRAPE = 3
ST_DOWNLOAD = 4
ST_WAIT = 5
ST_SEED = 6
ST_DONE = 7
ST_SEEDQUEUE = 8
ST_STOP = 9
ST_ERROR = (2**32) - 1

class State:
    """
    Keeps track of a torrents network state.
    """

    def __init__(self, tor, peerID, port, ip = None):

        # Initial state
        self.state = ST_NONE

        # Torrent info
        self.torrent = tor

        # Clients peerID
        self.peerID = peerID

        # port client is listening on
        self.port = port

        # external IP specified by client
        self.ip = ip

        # Set up initial tracker
        self.tracker = tracker.Tracker(tor.tracker, 
                                        tor.backupTrackers,
                                        self.peerID,
                                        self.port,
                                        self.ip)

        # List of dicts { ip, port } if in compressed mode
        # list of dicts { peerid, ip, port} if not
        #self.peers = []

        # Total downloaded
        self.totalDownloaded = 0

        # Total uploaded
        self.totalUploaded = 0

        self.state = ST_READY

    def setUserAgent(self, userAgent):
        self.tracker.userAgent = userAgent

    def setPeerID(self, peerID):
        self.peerID = peerID
        self.tracker.peerID = peerID

    def trackerScrape(self, numPeers):
        """
        Register us with the tracker,
        and scrape for peers.
        """

        self.state = ST_SCRAPE

        infoHash = self.torrent.hash
        left = self.torrent.length - self.totalDownloaded
        self.tracker.scrape(infoHash, 
                            self.totalUploaded, 
                            self.totalDownloaded, 
                            left, 
                            numPeers)

        self.state = ST_QUEUE

    def trackerStop(self):
        """
        Tells the tracker that we have completed the torrent.
        """

        infoHash = self.torrent.hash
        left = self.torrent.length = self.totalDownloaded
        self.tracker.stop(infoHash,
                          self.totalUploaded,
                          self.totalDownloaded,
                          left)

        self.state = ST_STOP

    def trackerComplete(self, numPeers):
        """
        Tels the tracker the torrent as having been completed.
        """

        infoHash = self.torrent.hash
        self.tracker.complete(infoHash,
                              self.totalUploaded,
                              self.torrent.length,
                              numPeers)
        
        self.state = ST_DONE

