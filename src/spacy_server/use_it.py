import socket
import comm


# send data to the server and receive a result
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# disable Nagle algorithm (probably only needed over a network)
# sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)
try:
    sock.connect((comm.server_host, comm.server_port))
    comm.send_data('this is a sentence', sock)
    result = comm.receive_data(sock)
    sock.close()

    # do something with the result...
    print(result.root)
except ConnectionRefusedError:
    print('nope')
