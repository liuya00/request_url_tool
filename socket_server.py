from threading import Thread
from urllib import request
import struct
import hashlib
import base64
import socket
import time

mode = "initialize"
picSize = 0
picReceive = 0
pic = ""
picRepeat = []


class returnCrossDomain(Thread):
    def __init__(self, connection):
        Thread.__init__(self)
        self.con = connection
        self.isHandleShake = False
        self.num = 0

    def run(self):
        global mode
        global picSize
        global picReceive
        global pic
        global picRepeat
        while True:
            if not self.isHandleShake:
                # Initial handshake
                header = self.analyzeReq()
                secKey = header['Sec-WebSocket-Key'];
                acceptKey = self.generateAcceptKey(secKey)

                response = "HTTP/1.1 101 Switching Protocols\r\n"
                response += "Upgrade: websocket\r\n"
                response += "Connection: Upgrade\r\n"
                response += "Sec-WebSocket-Accept: %s\r\n\r\n" % (acceptKey.decode('utf-8'))
                self.con.send(response.encode())
                self.isHandleShake = True
                if (mode == "initialize"):
                    mode = "get_order"
                print('response:\r\n' + response)
                # End of handshake

            # Read command phase
            elif mode == "get_order":
                opcode = self.getOpcode()
                if opcode == 8:
                    self.con.close()
                self.getDataLength()
                clientData = self.readClientData()
                print('clientData：' + str(clientData))
                # handle data

                ans = self.answer(clientData)
                self.sendDataToClient(str(ans))

    def analyzeReq(self):
        reqData = self.con.recv(1024).decode()
        reqList = reqData.split('\r\n')
        headers = {}
        for reqItem in reqList:
            if ': ' in reqItem:
                unit = reqItem.split(': ')
                headers[unit[0]] = unit[1]
        return headers

    def generateAcceptKey(self, secKey):
        sha1 = hashlib.sha1()
        sha1.update((secKey + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11').encode())
        sha1_result = sha1.digest()
        acceptKey = base64.b64encode(sha1_result)
        return acceptKey

    def getOpcode(self):
        first8Bit = self.con.recv(1)
        first8Bit = struct.unpack('B', first8Bit)[0]
        opcode = first8Bit & 0b00001111
        return opcode

    def getDataLength(self):
        second8Bit = self.con.recv(1)
        second8Bit = struct.unpack('B', second8Bit)[0]
        masking = second8Bit >> 7
        dataLength = second8Bit & 0b01111111
        if dataLength <= 125:
            payDataLength = dataLength
        elif dataLength == 126:
            payDataLength = struct.unpack('H', self.con.recv(2))[0]
        elif dataLength == 127:
            payDataLength = struct.unpack('Q', self.con.recv(8))[0]
        self.masking = masking
        self.payDataLength = payDataLength

    def readClientData(self):

        if self.masking == 1:
            maskingKey = self.con.recv(4)
        data = self.con.recv(self.payDataLength)

        if self.masking == 1:
            i = 0
            trueData = ''
            for d in data:
                trueData += chr(d ^ maskingKey[i % 4])
                i += 1
            return trueData
        else:
            return data

    def sendDataToClient(self, text):
        sendData = ''
        sendData = struct.pack('!B', 0x81)

        length = len(text)
        if length <= 125:
            sendData += struct.pack('!B', length)
        elif length <= 65536:
            sendData += struct.pack('!B', 126)
            sendData += struct.pack('!H', length)
        elif length == 127:
            sendData += struct.pack('!B', 127)
            sendData += struct.pack('!Q', length)

        sendData += struct.pack('!%ds' % (length), text.encode())
        dataSize = self.con.send(sendData)

    def answer(self, url):
        user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 " \
                     "(KHTML, like Gecko) Chrome/74.0.3729.157 Safari/537.36"
        referer = "<>"
        header = {
            # 'Referer': referer,
            'user-agent': user_agent
        }
        req = request.Request(url, headers=header)
        self.num += 1
        return self.num


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('127.0.0.1', 9999))
    sock.listen(5)
    while True:
        try:
            connection, address = sock.accept()
            returnCrossDomain(connection).start()
        except:
            time.sleep(1)


if __name__ == "__main__":
    main()
