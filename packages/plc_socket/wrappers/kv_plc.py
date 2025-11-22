import socket
import threading

class kv_plc_tcp_socket:
    def __init__(self, ipv4_address: str, port_number: int, timeout: int | None = None):
        '''
        When instance, this object opens a TCP socket connection.
        Includes methods for reading and writting KV-8000 R, MR, and DM memory devices:
        read(),
        write(),
        multi_read(),
        and multi_write().
        '''
        self.__valid_devices = ('R', 'MR', 'DM')
        self.__address = ipv4_address
        self.__port_number = port_number
        self.__timeout = timeout if timeout is not None else 3
        self.__socket = socket.create_connection((self.__address, self.__port_number), timeout=self.__timeout)
        self.__lock = threading.Lock()

    def __del__(self):
        self.__socket.close()

    def close_socket(self):
        self.__socket.close()

    def read(self, device: str, device_number: int) -> int:
        '''
        Parameters:
        device parameter can be 'R' or 'MR' or 'DM',
        device_number points the single device address to be read,
        read() method return value is the value read from the device address
        '''
        # Check that device matches one of the supported by the class
        if device not in self.__valid_devices:
            raise ValueError(f'Unsupported device type {device}')
        
        # Use lock context manager from thread module to avoid race conditions in socket buffer
        with self.__lock:
            # Send message from socket
            self.__socket.sendall(f'RD {device}{device_number}\r'.encode('ascii'))
            server_response = self.__socket.recv(1024)

        # Check for empty response before decoding
        if server_response == b'':
            raise Exception('Connection closed by peer')
        
        # Decode and strip successfully receive message
        buffer_value = server_response.decode('ascii').strip()

        match device:
            case 'R':
                return bool(int(buffer_value))
            case 'MR':
                return bool(int(buffer_value))
            case 'DM':
                return int(buffer_value)
            case _:
                raise ValueError(f'Unsupported device type {device}')
            
    def write(self, device: str, device_number: int, data: bool | int):
        '''
        Parameters:
        device parameter can be 'R' or 'MR' or 'DM',
        device_number points the single device address to be written,
        data is the value that will be written in the device address
        '''
        # Check that device parameter matches one of the supported by the class
        if device not in self.__valid_devices:
            raise ValueError(f'Unsupported device type {device}')
        
        #Check that data matches the device type
        match device:
            case 'R':
                if not(type(data) == bool or type(data) == int):
                    raise ValueError(f'Unsupported device value, {device} data value must match bool class or int class with a value of 0 or 1')
                elif type(data) == int and not(data == 0 or data == 1):
                    raise ValueError(f'Unsupported device value, {device} with data int class must have a value of 0 or 1')
            case 'MR':
                if not(type(data) == bool or type(data) == int):
                    raise ValueError(f'Unsupported device value, {device} data value must match bool class or int class with a value of 0 or 1')
                elif type(data) == int and not(data == 0 or data == 1):
                    raise ValueError(f'Unsupported device value, {device} with data int class must have a value of 0 or 1')
            case 'DM':
                if type(data) != int:
                    raise ValueError(f'Unsupported device value, {device} data value must match int class')
                elif type(data) == int and not (0 <= data <= 65535):
                    raise ValueError(f'Unsupported device value, {device} with data value {data} is out of range')
        
        # Process the value to be sent accordingly to the data type of the data parameter
        data_value = data

        if type(data_value) == bool:
            data_value = str(int(data))
        elif type(data_value) == int:
            data_value = str(data)

        # Use lock context manager from thread module to avoid race conditions in socket buffer
        with self.__lock:
            # Send message from socket
            self.__socket.sendall(f'WR {device}{device_number} {data_value}\r'.encode('ascii'))
            server_response = self.__socket.recv(1024) # Wait for server response just to take out the message from the socket buffer

        if server_response == b'':
            raise Exception('Connection closed by peer')
        
    def multi_read(self, device: str, device_number: int, number_of_devices: int) -> list[int]:
        # Check that device matches one of the supported by the class
        if device not in self.__valid_devices:
            raise ValueError(f'Unsupported device type {device}')
        
        list_of_values = []

        for i in range(0, number_of_devices):
            list_of_values.append(self.read(device, device_number + i))

        return list_of_values

    def multi_write(self, device: str, device_number: int, data_list: list[int]):
        # Check that device matches one of the supported by the class
        if device not in self.__valid_devices:
            raise ValueError(f'Unsupported device type {device}')
        
        # Infer the number of devices to be written from the data list length
        number_of_devices = len(data_list)
        
        for i in range(0, number_of_devices):
            self.write(device, device_number + i, data_list[i])