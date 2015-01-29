"""
Defines handlers for interacting with BT trackers

Copyright (C) 2007 Matt Waddell
ALL RIGHTS RESERVED
"""

import urllib2,urllib,socket,struct,urlparse,gzip,StringIO
import bencode, torrent

userAgent = 'PyBTOMG/0001'

EVENT_START = 'started'
EVENT_STOP = 'stopped'
EVENT_DONE = 'completed'
EVENT_UPDATE = '' 

class Tracker:
    """
    Provides an interface to interact with
    a BT tracker
    """

    def __init__(self, 
                tracker, 
                backupTrackers, 
                peerID, 
                port, 
                ip = None, 
                key = None):
        """
        Initializes the tracker object... Thats it.
        """

        self.tracker = tracker
        self.backupTrackers = backupTrackers
        self.peerID = peerID

        # Port the client is listening on
        self.port = port

        # External IP of the client to announce (optional)
        self.ip = ip

        # User agent used when contacting tracker
        self.userAgent = userAgent

        # Key to be used to identify the client
        self.key = key
        
        ### Data from interacting with tracker ###

        self.lastFailure = ''
        self.lastWarning = ''

        # Suggested interval to wait between polls
        self.interval = None

        # Mandatory interval to wait between polls
        self.minInterval = None

        # If present, must address the tracker as:
        self.trackerID = None 

        # Number of peers that completed DL
        self.complete = None 

        # Number of peers that haven't completed DL
        self.incomplete = None

        # Ask for a compressed peer list?
        self.getCompressedPeerList = True

        # Flag to not retrieve peer_ids of peers
        # if getCompressedPeerList is False
        self.noPeerID = True

        # If tracker is responding in compressed or regular mode
        # peers list returned { ip, port } if in compressed mode
        # { peerid, ip, port} if not and noPeerID is False
        self.compressedPeerList = False

    def update(self, infoHash, uploaded, downloaded, left, numwant):
        """
        Sends an update announcement to the tracker.
        Sets internal tracker state.

        Raises exception on failure
        """

        # A null event specifies an update
        try:
            comp,res = self.__sendRequest(infoHash, 
                                    uploaded, 
                                    downloaded, 
                                    left, 
                                    EVENT_UPDATE, 
                                    numwant)
        except Exception, msg:
            self.lastFailure = str(msg)
            raise Exception, msg

        if 'warning message' in res:
            self.lastWarning = res['warning message']

        self.CompressedPeerList = comp

        # Expect at least a list of peers
        # and an interval
        self.peers = res['peers']

        self.interval = res['interval']

        if 'min interval' in res:
            self.minInterval = res['min interval']

        if 'tracker id' in res:
            self.trackerID = res['tracker id']

        if 'complete' in res:
            self.complete = res['complete']

        if 'incomplete' in res:
            self.incomplete = res['incomplete']

    def scrape(self, infoHash, uploaded, downloaded, left, numwant):
        """
        Sends a start announcement to the tracker.
        Sets internal tracker state.

        Raises exception on failure
        """

        # A null event specifies an update
        try:
            comp,res = self.__sendRequest(infoHash, 
                                    uploaded, 
                                    downloaded, 
                                    left, 
                                    EVENT_START, 
                                    numwant)
        except Exception, msg:
            self.lastFailure = str(msg)
            raise Exception, msg

        if 'warning message' in res:
            self.lastWarning = res['warning message']

        self.CompressedPeerList = comp

        # Expect at least a list of peers
        # and an interval
        self.peers = res['peers']

        self.interval = res['interval']

        if 'min interval' in res:
            self.minInterval = res['min interval']

        if 'tracker id' in res:
            self.trackerID = res['tracker id']

        if 'complete' in res:
            self.complete = res['complete']

        if 'incomplete' in res:
            self.incomplete = res['incomplete']

    def stop(self, infoHash, uploaded, downloaded, left):
        """
        Sends stop announcement to the tracker.
        Sets internal tracker state.

        Raises exception on failure
        """

        # A null event specifies an update
        try:
            comp,res = self.__sendRequest(infoHash, 
                                    uploaded, 
                                    downloaded, 
                                    left, 
                                    EVENT_STOP, 
                                    0)
        except Exception, msg:
            self.lastFailure = str(msg)
            raise Exception, msg

        if 'warning message' in res:
            self.lastWarning = res['warning message']

        self.peers = []
        self.interval = None
        self.minInterval = None
        self.trackerID = None
        self.complete = None
        self.incomplet = None

    def complete(self, infoHash, uploaded, downloaded, numwant):
        """
        Sends a completed announcement to the tracker.
        Sets internal tracker state.

        Raises exception on failure
        """

        # A null event specifies an update
        try:
            comp,res = self.__sendRequest(infoHash, 
                                    uploaded, 
                                    downloaded, 
                                    0, 
                                    EVENT_DONE, 
                                    numwant)
        except Exception, msg:
            self.lastFailure = str(msg)
            raise Exception, msg

        if 'warning message' in res:
            self.lastWarning = res['warning message']

        self.CompressedPeerList = comp

        # Expect at least a list of peers
        # and an interval
        self.peers = res['peers']

        self.interval = res['interval']

        if 'min interval' in res:
            self.minInterval = res['min interval']

        if 'tracker id' in res:
            self.trackerID = res['tracker id']

        if 'complete' in res:
            self.complete = res['complete']

        if 'incomplete' in res:
            self.incomplete = res['incomplete']

    def __sendRequest(self, infoHash, uploaded, downloaded, left, event, numwant):
        """
        Sends a request to a tracker, and
        returns:
        
        (compressed, dict)

        where compressed specifies if the dict contains
        a compressed peer list or not, and dict is the
        dictionary of response values.

        If something failes an exception will be thrown.
        """
        
        params = {
            'info_hash'     :   infoHash,
            'peer_id'       :   self.peerID,
            'port'          :   self.port,
            'uploaded'      :   uploaded,
            'downloaded'    :   downloaded,
            'left'          :   left,
            'compact'       :   int(self.getCompressedPeerList),
            'no_peer_id'    :   int(self.noPeerID)
        }

        # Add the optional parameters
        if event:
            params['event'] = event
        if self.ip:
            params['ip'] = self.ip
        if numwant:
            params['numwant'] = numwant
        if self.key:
            params['key'] = self.key
        if self.trackerID:
            params['trackerid'] = self.trackerID

        headers = {
            #'Content-type'  :   'application/x-www-form-urlencoded',
            'User-Agent'        :   self.userAgent,
            'Accept'            :   'text/plain',
            'Connection'        :   'close',
            'Accept-Encoding'   :   'gzip'
        }

        # Construct the get string
        vars = []
        for key,val in params.items():
            vars.append('%s=%s' % (urllib.quote(key), urllib.quote(str(val))))

        # inspect the supplied tracker url
        # (it will always have a protocol extension)
        (scheme, dom, path, params, query, fragment) = urlparse.urlparse(self.tracker)

        # If a query string is already present, append to it
        if query:
            get = '&'.join(vars)
        else:
            get = '?' + '&'.join(vars)
        t = self.tracker + get

        try:
            req = urllib2.Request(t, None, headers)
            opener = urllib2.build_opener()
            fd = opener.open(req)

            # Check to see if the data was compressed 
            #

            encoding = fd.headers.get('Content-Encoding')
            if encoding == 'gzip':
                # Data was compressed with gzip
                compressed = fd.read()
                stream = StringIO.StringIO(compressed)
                zipper = gzip.GzipFile(fileobj = stream)
                data = zipper.read()
            else:
                # Assume data is not compressed?
                data = fd.read()

            try:
                dic = bencode.decode(data)
            except Exception, msg:
                raise Exception, 'Unrecognizable response: %s' % str(msg)

            # Check out the response
            if 'failure reason' in dic:
                raise Exception, dic['failure reason']

            compressed = False
            # Check to see if the reponse is compressed.
            # If the peers key is a string, the peers list
            # is compressed otherwise assume its a list of dicts
            if isinstance(dic['peers'], str):
                compressed = True
                # 4 bytes per IP,
                # 2 bytes per port.

                hostEntLen = 6

                dLen = len(dic['peers'])
                if dLen % hostEntLen != 0:
                    raise Exception, 'Compressed peers list is malformed'
     
                peers = []
                # list of peers and ports dicts
                if dLen > 0:
                    i,j = 0, hostEntLen
                    while j < dLen:
                        hostEnt = dic['peers'][i:j]
                        i += hostEntLen
                        j += hostEntLen

                        # First 4 bytes -> ip (network byte order)
                        # Next 2 bytes -> port (network byte order)
                        ip = hostEnt[0:4]
                        ip = socket.inet_ntoa(ip)

                        port, = struct.unpack('H', hostEnt[4:6])
                        port = socket.ntohs(port)

                        h = {
                            'host'  : ip,
                            'port'  : port
                        }

                        peers.append(h)

                dic['peers'] = peers

        except Exception, msg:
            raise Exception, 'Tracker Error: %s' % str(msg)

        return (compressed, dic)

