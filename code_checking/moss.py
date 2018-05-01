import socket


class Moss:
    def __init__(self, user_id):
        self.server = 'moss.stanford.edu'
        self.port = 7690
        self.user_id = user_id
        self.options = {
            "l": "ascii",
            "m": 10,
            "d": 0,
            "x": 0,
            "c": "",
            "n": 250
        }
        self.base_files = []
        self.files = []

    def add_file(self, file_name, code):
        self.files.append((file_name, code))

    def upload_file(self, s, file_name, code, file_id):
        b_code = code.encode()
        size = len(b_code)
        message = "file {0} {1} {2} {3}\n".format(
            file_id,
            self.options['l'],
            size,
            file_name
        )
        s.send(message.encode())
        s.send(b_code)

    def send(self):
        s = socket.socket()
        s.connect((self.server, self.port))
        s.send("moss {}\n".format(self.user_id).encode())
        s.send("directory {}\n".format(self.options['d']).encode())
        s.send("X {}\n".format(self.options['x']).encode())
        s.send("maxmatches {}\n".format(self.options['m']).encode())
        s.send("show {}\n".format(self.options['n']).encode())
        s.send("language {}\n".format(self.options['l']).encode())
        recv = s.recv(1024)
        if recv == "no":
            s.send(b"end\n")
            s.close()
            raise Exception("send() => Language not accepted by server")
        index = 1
        for file_name, code in self.files:
            self.upload_file(s, file_name, code, index)
            index += 1
        s.send("query 0 {}\n".format(self.options['c']).encode())
        response = s.recv(1024)
        s.send(b"end\n")
        s.close()
        return response.decode().replace("\n", "")
