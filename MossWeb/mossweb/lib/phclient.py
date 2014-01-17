'''
Created on Feb 4, 2011

@author: chuck
'''
import socket


class PHClient:

    def __init__(self):
        self.sock = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        self.sock.connect(("webapps.cs.uiuc.edu", 105))

    def query(self, netid):
        self.sock.send("query netid="+netid+" return all\n")
        msg = self.__recv()
        msg = msg[(msg.find('\n')+1):]
        msg = msg[:msg.rfind('\n')]
        msg = msg[:msg.rfind('\n')]
        msg = msg.replace("-200:1:", "")
        return msg

    def __recv(self):
        msg = ''
        while True:
            chunk = self.sock.recv(4096)
            msg += chunk
            if '200:Ok.' in chunk or '501:No' in chunk:
                break
        return msg
    
    def disconnect(self):
        self.sock.close()


def main():
    s = PHClient()
    try:
        s.connect()
        print s.query("alamber3")
    except:
        pass
    s.disconnect()

if __name__ == '__main__':
    main()