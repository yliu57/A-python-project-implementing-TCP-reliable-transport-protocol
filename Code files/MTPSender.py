# Group member:
#
# Qiaodan Xie, G01241409
# Xueyuan He, G01248547
# Yuxi Liu, G01223126
## The code provided here is just a skeleton that can help you get started
## You can add/remove functions as you wish


## import (add more if you need)
import threading
import unreliable_channel
import zlib
import socket
import sys
import binascii



## define and initialize
# window_size, window_base, next_seq_number, dup_ack_count, etc.
# client_port

next_seq_number = 0
window_base = 0
dup_ack_count = 0
packet_size = 0
client_port = 80
lf = 0
recv_addr = ()
packets = []
count = 0
window_size = 0
i = 0
window_status = dict()

## we will need a lock to protect against concurrent threads
lock = threading.Lock()

def update_window():
    text = "Updating window;\nWindow state: ["
    n = 0
    for key in window_status.keys():
        if n < window_size:
            text += (str(key) + "(" + str(window_status[key]) + ")" + ", ")
        n += 1
    text += "]"
    lf.write(text + "\n")


def create_packet(data, seq_num):
# Two types of packets, data and ack
# crc32 available through zlib library
    types = 0
    seq = seq_num
    length = len(data)
    types = types.to_bytes(4, byteorder="big")
    seq = seq.to_bytes(4, byteorder="big")
    length = length.to_bytes(4, byteorder="big")
    data = data.encode('utf-8')
    total = types + seq + length + data
    checkSum = zlib.crc32(total)
    checkSum = checkSum.to_bytes(4, byteorder="big")
    packet = types + seq + length +checkSum + data
    return packet

def checksum_calculator(types_, seq_, length_):
# Two types of packets, data and ack
# crc32 available through zlib library
    if(types_ == "DATA"):
        types_ = 0
    elif types_ == "ACK":
        types_ = 1
    types_ = types_.to_bytes(4, byteorder="big")
    seq_ = seq_.to_bytes(4, byteorder="big")
    length_ = length_.to_bytes(4, byteorder="big")
    total_ = types_ + seq_ + length_
    checkSum_ = zlib.crc32(total_)
    # checkSum = checkSum.to_bytes(4, byteorder="big")

    return checkSum_
    


def extract_packet_info(received_packet):
# extract the packet data after receiving
    hex_packet = binascii.hexlify(received_packet).decode("utf-8")
    types = hex_packet[0:8]
    hex_packet = hex_packet[8:]
    seq = hex_packet[0:8]
    hex_packet = hex_packet[8:]
    length = hex_packet[0:8]
    hex_packet = hex_packet[8:]
    checkSum = hex_packet[0:8]
    status = hex_packet[8:]  # hex str ?
    
    
    
    types = int(types,16)
    if types == 0:
        types_ret = "DATA"
    else:
        types_ret = "ACK"
        
    seq = int(seq,16)
    length = int(length,16)
    checkSum = int(checkSum, 16)
    status = bytes.fromhex(status)
    
    return types_ret, seq, length, checkSum, status
    


def receive_thread(sock):
    global window_base
    global dup_ack_count
    global packet_size
    global next_seq
    global count
    global i
    packets_buffer = []
    duplicate = -1
    flag = 0
    while True:
        # receive packet, but using our unreliable channel
        # packet_from_server, server_addr = unreliable_channel.recv_packet(socket)
        # call extract_packet_info
        # check for corruption, take steps accordingly
        # update window size, timer, triple dup acks

        # try:
        #     print("enter thread...........")
        #     while True:
        #         if flag == 0:
        #             packet_from_server, server_addr = unreliable_channel.recv_packet(sock)
        #         elif flag == 1 and len(packets_buffer) > 0:
        #             packet_from_server = packets_buffer.pop(0)
        #         if len(packets_buffer) == 0:
        #             flag = 0
        #         #socket.setdefaulttimeout(0.5)
        #         print("1")
        #         types, seq, length, checkSum, status = extract_packet_info(packet_from_server)
        #         calc_checksum = checksum_calculator(types, seq, length)
        #         print("calc_checksum: ", calc_checksum)
        #         print("checkSum: ", checkSum)
        #         # if status != "corrupted!":
        #         if calc_checksum == checkSum:
        #             if seq-1 == window_base:
        #                 flag = 1
        #                 lock.acquire()
        #                 if packet_size < window_size:
        #                     window_status.pop(window_base)
        #                     packet_size += 1
        #                     window_base += 1
        #                 lock.release()
        #                 text = "Packet received; type=ACK; seqNum=" + str(seq) + ";length=" + str(
        #                     length) + ";checksum_in_packet=" + str(checkSum)
        #                 lf.write(text + "\n")
        #                 update_window()
        #             else:
        #                 packets_buffer.append(packet_from_server)
        #
        #             if duplicate != seq:
        #                 duplicate = seq
        #                 dup_ack_count = 0
        #             if duplicate == seq:
        #                 dup_ack_count += 1
        # except socket.timeout:
        #     unreliable_channel.send_packet(sock, packets[window_base], recv_addr)
        #     text = "Timeout for packet seqNum=" + str(seq)
        #     lf.write(text + "\n")
        try:
            # print("enter thread...........")
            if count == 0:
                break
            packet_from_server, server_addr = unreliable_channel.recv_packet(sock)
            #socket.setdefaulttimeout(0.5)
            # print("1")
            types, seq, length, checkSum, status = extract_packet_info(packet_from_server)
            calc_checksum = checksum_calculator(types, seq, length)
            # print("calc_checksum: ", calc_checksum)
            # print("checkSum: ", checkSum)
            # if status != "corrupted!":
            if calc_checksum == checkSum:
                if seq-1 == window_base:
                    lock.acquire()
                    if packet_size < window_size:
                        window_status.pop(window_base)
                        packet_size += 1
                        window_base += 1
                        count -= 1
                        i = window_base
                    lock.release()
                    text = "Packet received; type=ACK; seqNum=" + str(seq) + ";length=" + str(
                        length) + ";checksum_in_packet=" + str(checkSum)
                    lf.write(text + "\n")
                    update_window()

                if duplicate != seq:
                    duplicate = seq
                    dup_ack_count = 0
                if duplicate == seq:
                    dup_ack_count += 1
        except socket.timeout:
            if count == 0:
                break
            unreliable_channel.send_packet(sock, packets[window_base], recv_addr)
            text = "Timeout for packet seqNum=" + str(seq)
            lf.write(text + "\n")

def main():
	# read the command line arguments
    global packet_size
    global window_size
    global window_base
    global next_seq_number
    global dup_ack_count
    global window_status
    global next_seq
    global client_port
    global lf
    global recv_addr
    global packets
    global count
    global i

    receiver_ip = sys.argv[1]
    receiver_port =int(sys.argv[2])
    packet_size = int(sys.argv[3])
    window_size = int(sys.argv[3])
    input_file = sys.argv[4]
    log_file = sys.argv[5]
    

    packets = []

    recv_addr = (receiver_ip, receiver_port)

	# open log file and start logging
    lf = open(log_file, 'w')

	# open client socket and bind
    sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    #sock.bind((receiver_ip,receiver_port))
    #socket.setdefaulttimeout(0.5)
    sock.settimeout(0.5)
    # # start receive thread
    # recv_thread = threading.Thread(target=receive_thread,args=(sock,))
    # recv_thread.start()

    # take the input file and split it into packets (use create_packet)
    
    f = open(input_file, "r")
    
    while True:
        data = f.read(1456)
        if not data:
            break
        packets.append(create_packet(data, next_seq_number))
        window_status[next_seq_number] = 1
        next_seq_number += 1
    count = len(packets)

    # start receive thread
    recv_thread = threading.Thread(target=receive_thread, args=(sock,))
    recv_thread.start()

	# while there are packets to send:
		# send packets to server using our unreliable_channel.send_packet() 


    while count >= 0:
        print("count total packets left: ", count)
        if count == 0:
            break
        while packet_size > 0:
            try:
                # print("enter while")
                if i < len(packets):
                    types_ret, seq, length, checkSum, status = extract_packet_info(packets[i])
                    if dup_ack_count != 3:
                        # print("enter dup")
                        unreliable_channel.send_packet(sock, packets[i], recv_addr)
                        # count -= 1
                        window_status[seq] = 0
                        text = "Packet sent; type=DATA; seqNum=" + str(seq) + ";length=" + str(length) + ";checksum_in_packet=" + str(checkSum)
                        lf.write(text + "\n")
                    else:
                        unreliable_channel.send_packet(sock, packets[window_base], recv_addr)
                        # i = window_base
                        text = "Triple dup acks received for packet seqNum=" + str(seq)
                        lf.write(text + "\n")

            except socket.timeout:
                print("you should not be here-------------------------------------------------------")
                    # unreliable_channel.send_packet(sock, packets[window_base], recv_addr)
                    # text = "Timeout for packet seqNum=" + seq
                    # lf.write(text + "\n")

        # update the window size, timer, etc.
            lock.acquire()
            packet_size -= 1
            lock.release()
            i += 1
    
    sock.close()
    lf.close()

if __name__ == "__main__":
    main()



