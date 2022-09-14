# Group member:
#
# Qiaodan Xie, G01241409
# Xueyuan He, G01248547
# Yuxi Liu, G01223126
## The code provided here is just a skeleton that can help you get started
## You can add/remove functions as you wish

## import (add more if you need)
import unreliable_channel
import threading
import unreliable_channel
import zlib
import socket
import sys
import binascii

## we will need a lock to protect against concurrent threads
lock = threading.Lock()

def create_packet(seq_num):
# Two types of packets, data and ack
# crc32 available through zlib library
	types = 1
	seq = seq_num
	length = 0
	types = types.to_bytes(4, byteorder="big")
	seq = seq.to_bytes(4, byteorder="big")
	length = length.to_bytes(4, byteorder="big")
	total = types + seq + length
	checkSum = zlib.crc32(total)
	checkSum = checkSum.to_bytes(4, byteorder="big")
	packet = types + seq + length + checkSum

	return packet


def checksum_calculator(types, seq, length, data):
# Two types of packets, data and ack
# crc32 available through zlib library
	if(types == "DATA"):
		types_ = 0
	elif types == "ACK":
		types_ = 1
	types_ = types_.to_bytes(4, byteorder="big")
	seq = seq.to_bytes(4, byteorder="big")
	length = length.to_bytes(4, byteorder="big")

	# print("types_: , seq: , length: , data: ", type(types_), type(seq), type(length), type(data))
	total = types_ + seq + length + data
	checkSum = zlib.crc32(total)

	return checkSum


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

	types = int(types, 16)
	if types == 0:
		types_ret = "DATA"
	else:
		types_ret = "ACK"

	seq = int(seq, 16)
	length = int(length, 16)
	checkSum = int(checkSum, 16)
	status = bytes.fromhex(status)

	return types_ret, seq, length, checkSum, status

def main():
	# read the command line arguments
	# print("0")

	receiver_port = int(sys.argv[1])
	output_file = sys.argv[2]
	log_file = sys.argv[3]

	temp_packet = create_packet(0)
	expected_seq = 0
	# client_addr = ()
	# client_port = int(receiver_port)
	localIP = "127.0.0.1"
# 	hostname = socket.gethostname()
# 	localIP = socket.gethostbyname(hostname)

	recv_addr = (localIP, receiver_port)

	# open log file and start logging
	lf = open(log_file, 'w')
	output = open(output_file, "w")
	# open server socket and bind

	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock.bind((localIP, receiver_port))
	#socket.setdefaulttimeout(0.5)
	sock.settimeout(0.5)

	while True:

		# receive packet, but using our unreliable channel
		# packet_from_server, server_addr = unreliable_channel.recv_packet(socket)
		# call extract_packet_info
		# check for corruption and lost packets, send ack accordingly
		try:
			# print("1.5")
			# if(sock.connect_ex() == 0):
			# 	sock.close()
			# 	lf.close()
			# 	output.close()
			# 	break
			packet_from_server, client_addr = unreliable_channel.recv_packet(sock)
			types_ret, seq, length, checkSum, status = extract_packet_info(packet_from_server)
			# print("types_ret, seq, length, checkSum: ", types_ret,seq,length,checkSum)
			# print("checkSum type: ", type(checkSum))
			calc_checksum = checksum_calculator(types_ret, seq, length, status)


			if calc_checksum == checkSum and expected_seq == seq:
				# print("2")
				text = "Packet received; type=DATA; seqNum=" + str(seq) + "; length=" + str(length) + \
					"; checksum_in_packet=" + str(checkSum) + "; checksum_calculated =" + str(calc_checksum) + "; status=NOT_CORRUPT"
				lf.write(text + "\n")
				status = status.decode("utf-8")
				output.write(status)
				seq += 1
				expected_seq = seq
				packet = create_packet(seq)
				temp_packet = packet
				unreliable_channel.send_packet(sock, packet, client_addr)

				text = "Packet sent; type=ACK; seqNum=" + str(seq) + "; length=" + str(length) + \
						"; checksum_in_packet=" + str(checkSum) + ";"
				lf.write(text + "\n")

			elif calc_checksum == checkSum and expected_seq != seq:
				while True:
					unreliable_channel.send_packet(sock, temp_packet, client_addr)
					text = "Packet sent; type=ACK; seqNum=" + str(expected_seq) + "; length=" + str(length) + \
						   "; checksum_in_packet=" + str(checkSum) + "; checksum_calculated =" + str(
						calc_checksum) + "; status=OUT_OF_ORDER_PACKET"
					lf.write(text + "\n")
					packet_from_server, client_addr = unreliable_channel.recv_packet(sock)
					types_ret, seq, length, checkSum, status = extract_packet_info(packet_from_server)
					if seq == expected_seq:
						calc_checksum = checksum_calculator(types_ret, seq, length, status)
						if calc_checksum == checkSum and expected_seq == seq:
							# print("2")
							text = "Packet received; type=DATA; seqNum=" + str(seq) + "; length=" + str(length) + \
								   "; checksum_in_packet=" + str(checkSum) + "; checksum_calculated =" + str(
								calc_checksum) + "; status=NOT_CORRUPT"
							lf.write(text + "\n")
							status = status.decode("utf-8")
							output.write(status)
							seq += 1
							expected_seq = seq
							packet = create_packet(seq)
							temp_packet = packet
							unreliable_channel.send_packet(sock, packet, client_addr)

							text = "Packet sent; type=ACK; seqNum=" + str(seq) + "; length=" + str(length) + \
								   "; checksum_in_packet=" + str(checkSum) + ";"
							lf.write(text + "\n")
							# lock.release()
							break

			else:
				unreliable_channel.send_packet(sock, temp_packet, client_addr)
				text = "Packet sent; type=ACK; seqNum=" + str(seq) + "; length=" + str(length) + \
						"; checksum_in_packet=" + str(checkSum) + "; checksum_calculated =" + str(calc_checksum) + "; status=CORRUPT"
				lf.write(text + "\n")

		except socket.timeout:
			print("receiving...")
			if temp_packet != create_packet(0):
				unreliable_channel.send_packet(sock, temp_packet, client_addr)
		except ConnectionResetError as e:
			print("connection closed")
			sock.close()
			lf.close()
			output.close()
			break


if __name__ == "__main__":
    main()







