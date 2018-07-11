import random
import struct
import itertools


class WebsocketHandler:
    def __init__(self, transport):
        self.parser = FrameParser(self)
        self.transport = transport

    async def feed(self, data: bytes):
        await self.parser.feed(data)

    async def on_message(self, data):
        pass

    async def on_close(self):
        pass

    async def on_connect(self):
        pass

    async def send(self, data: bytes):
        """

        :param data:
        :return:
        """
        # This method is a co-routine to give the opportunity
        # to the underlying buffer be flushed into the socket.
        frame = create_single_frame(data)
        self.transport.write(frame)


def create_single_frame(data, mask=False, opcode: int = None):

    frame = bytearray()

    # Frame options.
    if opcode is None:
        if isinstance(data, str):
            head1 = 0b10000000 | 0 | 0 | 0 | 1
            data = data.encode("utf-8")
        else:
            head1 = 0b10000000 | 0 | 0 | 0 | 2
    else:
        if isinstance(data, str):
            data = data.encode("utf-8")
        head1 = 0b10000000 | 0 | 0 | 0 | opcode

    head2 = 0b10000000 if mask else 0

    # Length headers
    length = len(data)
    if length < 126:
        frame.extend(struct.pack("!BB", head1, head2 | length))
    elif length < 65536:
        frame.extend(struct.pack("!BBH", head1, head2 | 126, length))
    else:
        frame.extend(struct.pack("!BBQ", head1, head2 | 127, length))

    # Masking the data to create some entropy.
    if mask:
        mask_bits = struct.pack("!I", random.getrandbits(32))
        frame.extend(mask_bits)
        data = bytes(b ^ m for b, m in zip(data, itertools.cycle(mask_bits)))

    frame.extend(data)

    return frame


class Status:
    FIRST_TWO_BYTES = 0
    LENGTH_126 = 1
    LENGTH_127 = 2
    MASK = 3
    PAYLOAD = 4


class FrameParser:
    def __init__(self, protocol):
        self.data = bytearray()
        self.protocol = protocol

        self.final = None
        self.rsv1 = None
        self.rsv2 = None
        self.rsv3 = None
        self.opcode = None
        self.masked = None
        self.mask = None
        self.payload_length = None
        self.payload = bytearray()

        self.opcode_handlers = {
            9: self._handle_ping,
            1: self._handle_text,
            2: self._handle_binary,
            8: self._handle_close,
        }

        self.status = Status.FIRST_TWO_BYTES

    @staticmethod
    def apply_mask(data, mask):
        """
        Apply masking to websocket message.
        """
        return bytes(b ^ m for b, m in zip(data, itertools.cycle(mask)))

    def clear(self):
        self.final = None
        self.rsv1 = None
        self.rsv2 = None
        self.rsv3 = None
        self.opcode = None
        self.masked = None
        self.mask = None
        self.payload_length = None
        self.payload = bytearray()
        self.status = Status.FIRST_TWO_BYTES

    async def feed(self, data: bytes):
        self.data.extend(data)
        length = len(self.data)

        # Expecting the first two bytes.
        if self.status == Status.FIRST_TWO_BYTES and length >= 2:
            head1, head2 = struct.unpack("!BB", data[:2])
            del self.data[:2]
            self.final = True if head1 & 0b10000000 else False
            self.rsv1 = True if head1 & 0b01000000 else False
            self.rsv2 = True if head1 & 0b00100000 else False
            self.rsv3 = True if head1 & 0b00010000 else False
            self.opcode = head1 & 0b00001111
            self.masked = True if head2 & 0b10000000 else False
            self.payload_length = head2 & 0b01111111
            if self.payload_length == 126:
                self.status = Status.LENGTH_126
            elif self.payload_length == 127:
                self.status = Status.LENGTH_127
            else:
                self.status = Status.MASK if self.masked else Status.PAYLOAD

        # Payload length 7+16 bits
        if self.status == Status.LENGTH_126 and length >= 2:
            self.payload_length = struct.unpack("!H", self.data[:2])
            del self.data[:2]
            self.status = Status.MASK if self.masked else Status.PAYLOAD

        # Payload length 7+64 bits
        if self.status == Status.LENGTH_127 and length >= 8:
            self.payload_length = struct.unpack("!Q", self.data[:8])
            del self.data[:8]
            self.status = Status.MASK if self.masked else Status.PAYLOAD

        # Extracting the payload mask
        if self.status == Status.MASK:
            self.mask = self.data[:4]
            del self.data[:4]
            self.status = Status.PAYLOAD

        # Expecting the payload itself
        if self.status == Status.PAYLOAD and length >= self.payload_length:
            print(f"Received opcode: {self.opcode}")
            print(f"Length: {self.payload_length}")
            print(f"Data: {self.data[:self.payload_length]}")
            decoded = ""
            for char in bytes(self.data[: self.payload_length]):
                char ^= self.mask[len(decoded) % 4]
                decoded += chr(char)
            del self.data[: self.payload_length]
            await self.opcode_handlers[self.opcode](decoded)
            # await self.handler.on_message(decoded.encode('utf-8'))
            self.clear()

    async def _handle_ping(self, msg):
        print("Received ping.")
        a = create_single_frame(msg, opcode=10)
        print(a)
        a.extend(b"1231233453453435353")
        await self.protocol.write(a)
        print("Sent pong.")

    async def _handle_text(self, msg):
        print(f"Received text: {msg}")

    async def _handle_binary(self, msg):
        print(f"Received binary {msg}")

    async def _handle_close(self, msg):
        print("Server is closing the connection")
