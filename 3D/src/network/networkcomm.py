import sys
import socket
import struct
import types
import cPickle as pickle
from cStringIO import StringIO
import select
import game

from replaydump import persistent_id, persistent_load

def send(channel, args):
    src = StringIO()
    p = pickle.Pickler(src, protocol=-1)
    p.persistent_id = persistent_id
    p.dump(args)
    buf = src.getvalue()
    if len(buf) == 0: print "Warning - sending data of size 0"
    value = socket.htonl(len(buf))
    size = struct.pack("l", value)
    nbytes = 0
    while True:
        nbytes += channel.send(size[nbytes:])
        if nbytes == len(size): break
    nbytes = 0
    while True:
        nbytes += channel.send(buf[nbytes:])
        if nbytes == len(buf): break

def receive(channel):
    numread = 0
    lsize = struct.calcsize("l")
    size = ''
    while True:
        size += channel.recv(lsize - numread)
        numread = len(size)
        if numread == lsize: break
    size = socket.ntohl(struct.unpack("l", size)[0])
    dst = StringIO()
    numread = 0
    while True:
        buf = channel.recv(size - numread)
        numread += len(buf)
        dst.write(buf)
        if numread == size: break
    dst.seek(0)
    p = pickle.Unpickler(dst)
    p.persistent_load = persistent_load
    obj = p.load()
    return obj

def send_new(channel, args):
    src = StringIO()
    p = pickle.Pickler(src, protocol=-1)
    p.persistent_id = persistent_id
    p.dump(args)
    data = src.getvalue()
    if len(data) == 0: print "Warning - sending data of size 0"
    res = channel.sendall(struct.pack('!i', len(data))+data)

def receive_new(channel):
    #data length is packed into 4 bytes
    total_len=0;total_data=[];size=sys.maxint
    size_data=sock_data='';recv_size=8192
    while total_len<size:
        sock_data=channel.recv(recv_size)
        if not total_data:
            if len(sock_data)>4:
                size_data+=sock_data
                size=struct.unpack('!i', size_data[:4])[0]
                recv_size=size
                if recv_size>524288:recv_size=524288
                total_data.append(size_data[4:])
            else:
                size_data+=sock_data
        else:
            total_data.append(sock_data)
        total_len=sum([len(i) for i in total_data ])
    dst = StringIO()
    dst.write(''.join(total_data))
    dst.seek(0)
    p = pickle.Unpickler(dst)
    p.persistent_load = persistent_load
    return p.load()

#send = send_new
#receive = receive_new

class Comm(object):
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.channel = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    def send(self, args):
        send(self.channel, args)
    def receive(self):
        return receive(self.channel)
    def poll_other(self):
        in_ready,out_ready,err_ready = select.select([self.channel], [], [], 0.005)
        if len(in_ready) > 0: return True
        else: return False
    def poll_other_2(self):
        result = self.poll.poll(50)
        if not result: return False
        else: return True
    def __del__(self):
        self.channel.close()

class Client(Comm):
    def __init__(self, ip, port):
        super(Client,self).__init__(ip, port)
        self.channel.connect((ip, port))

class Server(Comm):
    def __init__(self, ip, port):
        super(Server,self).__init__(ip, port)
        self.channel.bind(('', port))
        self.channel.listen(1)
        self.info = self.channel.getsockname()
        client = self.channel.accept()[0]
        self.channel.close()
        self.channel = client

def getipaddr(hostname='default'):
    """Given a hostname, perform a standard (forward) lookup and return
    a list of IP addresses for that host."""
    if hostname == 'default': hostname = socket.gethostname()
    try:
        ips = socket.gethostbyname_ex(hostname)[2]
        ips = [i for i in ips if i.split('.')[0] != '127']
        if len(ips) != 0:
            # check if we have succes in determining outside IP
            ip = ips[0]
    except socket.gaierror:
    # when we want to determine local IP and did not have succes
    # with gethostbyname_ex then we would like to connect to say
    # google.com and determine the local ip address bound to the
    # local socket.
        try:
            s = socket.socket()
            s.connect(('google.com', 80))
            ip = s.getsockname()[0]
            del s
        except:
            print ('*** cannot connect to internet in order to \
                    determine outside IP address')
            raise Exception
    if len(ip) != 0:
        return ip
    else:
        print ('*** unable to determine outside IP address')
        raise Exception

def test():
    import Zeroconf
    local_ip = getipaddr()
    server = Zeroconf.Zeroconf(local_ip)
    ipaddr = socket.inet_aton(local_ip)
    svc1 = Zeroconf.ServiceInfo('_incantus._tcp.local.',
                                  'Halcyon 1._incantus._tcp.local.',
                                  address = ipaddr,
                                  port = 5000,
                                  weight = 0, priority=0,
                                  properties = {'description': 'Incantus client'}
                                 )
    server.registerService(svc1)
