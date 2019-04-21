# This is the Twisted Get Poetry Now! client, version 1.0.
# NOTE: This should not be used as the basis for production code.
# It uses low-level Twisted APIs as a learning exercise.

import datetime, errno, optparse, socket, sys

from twisted.internet import main
def parse_args():
    usage = """usage: %prog [options] [hostname]:port ...
This is the Get Poetry Now! client, Twisted version 1.0.
Run it like this:
  python twisted-client-1/get-poetry.py 10001 10002 10003
"""
    parser = optparse.OptionParser(usage)
    _, addresses = parser.parse_args()
    if not addresses:
        print parser.format_help()
        parser.exit()
    def parse_address(addr):
        if ':' not in addr:
            host = '127.0.0.1'
            port = addr
        else:
            host, port = addr.split(':', 1)
        if not port.isdigit():
            parser.error('Ports must be integers.')
        return host, int(port)
    return map(parse_address, addresses)

class PoetrySocket(object):
    poem = ''
    def __init__(self, task_num, address):
        try:
            self.task_num = task_num
            self.address = address
            self.sock = socket.socket(socket.AF_INET,
                                      socket.SOCK_STREAM)
            self.sock.connect(address)
            self.sock.setblocking(0)
            from twisted.internet import reactor
            reactor.callLater(5, self.timeout)
        except socket.error, msg:
            print "Couldnt connect with the socket-server: %s\n terminating program" % msg
            self.sock = None


    def fileno(self):
        try:
            return self.sock.fileno()
        except socket.error:
            return -1

    def connectionLost(self, reason):
        self.sock.close()
        # stop monitoring this socket
        from twisted.internet import reactor
        reactor.removeReader(self)
        # see if there are any poetry sockets left
        for reader in reactor.getReaders():
            if isinstance(reader, PoetrySocket):
                return
        reactor.stop()  # no more poetry

    def doRead(self):
        bytes = ''
        while True:
            try:
                bytesread = self.sock.recv(1024)
                if not bytesread:
                    break
                else:
                    bytes += bytesread
            except socket.error, e:
                if e.args[0] == errno.EWOULDBLOCK:
                    break
                return main.CONNECTION_LOST

        if not bytes:
            print 'Task %d finished' % self.task_num
            return main.CONNECTION_DONE
        else:
            msg = 'Task %d: got %d bytes of poetry from %s'
            print  msg % (self.task_num, len(bytes), self.format_addr())

        self.poem += bytes

    def timeout(self):
        print "Task %d timeout." % self.task_num
        self.connectionLost('timeout')

    def logPrefix(self):
        return 'poetry'

    def format_addr(self):
        host, port = self.address
        return '%s:%s' % (host or '127.0.0.1', port)


def poetry_main():
    addresses = parse_args()
    start = datetime.datetime.now()
    sockets = [PoetrySocket(i+1, addr) for i, addr in enumerate(addresses)]

    from twisted.internet import reactor
    # tell the Twisted reactor to monitor this socket for reading
    for socket in sockets:
        if socket.sock:
            reactor.addReader(socket)
    reactor.run()

    elapsed = datetime.datetime.now() - start
    for i, sock in enumerate(sockets):
        print 'Task %d: %d bytes of poetry' % (i + 1, len(sock.poem))

    print 'Got %d poems in %s' % (len(addresses), elapsed)


if __name__ == '__main__':
    poetry_main()
