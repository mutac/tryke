"""
Inform a tracker
that you have uploaded an
arbitrary number of bytes
to a particular torrent.
"""

import bt.client
import sys, time

if __name__ == '__main__':
    if len(sys.argv) < 4:
        raise Exception, 'Too few arguments'

    torrent = sys.argv[1]
    port = int(sys.argv[2])
    sleep = int(sys.argv[3])

    cli = bt.client.Client(torrent, port)

    # Spoof peer id to look like the newest version of azureus
    cli.emulate('azureus')

    # Muck around with the state to make it appear as though 
    # most of the torrent has been downloaded, and that
    # a respectable amount has been uploaded.

    # Say we only downloaded one piece
    cli.state.totalDownloaded = 0

    # And we haven't uploaded anything yet
    cli.state.totalUploadeded = 0

    numPeers = 25

    print 'Tracker: %s' % cli.state.torrent.tracker
    print 'Torrent Size: %d bytes' % cli.state.torrent.length
    print 'File Name: %s' % cli.state.torrent.fileName
    if cli.state.torrent.fileMode == 'single-file':
        print 'Files: 1'
    else:
        print 'Files: %d' % len(cli.state.torrent.files)
    print ''
    
    # Now tell the tracker about ourselves
    print 'Announcing ourselves...'
    cli.state.trackerScrape(numPeers)
    print 'done'

    print ''
    
    print 'Waiting (%d)...' % sleep
    time.sleep(sleep)
    print ''
    
    # Finally tell the tracker we're stopping
    # after downloading only one piece, but
    # uploading it a bagillion times.
    cli.state.totalDownloaded = cli.state.torrent.pieceLen
    cli.state.totalUploaded = cli.state.totalDownloaded * 1000

    print 'Lying to tracker...'
    print 'Advertised "Downloaded": %d bytes' % cli.state.totalDownloaded
    print 'Advertised "Uploaded": %d bytes' % cli.state.totalUploaded
    cli.state.trackerStop()
    print 'done'

