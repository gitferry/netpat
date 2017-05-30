import sys
import socket
import getopt
import threading
import subprocess

isListen = False
isCommand = False
isUpload = False
execute_line = ""
target_name = ""
upload_path = ""
port_number = 0

def usage():
    # Help text
    print
    print "Usage: PyCat.py -t target_host -p port"
    print
    print "-h --help"
    print "Display this help message"
    print
    print "-l --listen"
    print "Listen on [host]:[port] for incoming connections"
    print
    print "-c --command"
    print "Initialize a command shell"
    print
    print "-e --execute=file_to_run"
    print "Execute file upon connection"
    print
    print "-u --upload=destination"
    print "Upon connection upload file and write to [destination]"
    print
    print "Examples: "
    print "netpat.py -t 192.168.0.1 -p 5555 -l -c"
    print "netpat.py -t 192.168.0.1 -p 5555 -l -u=c:\\target.exe"
    print "netpat.py -t 192.168.0.1 -p 5555 -l -e=\"cat /etc/passwd\""
    print "echo 'ABCDEFGHI' | ./netpat.py -t 192.168.11.12 -p 135"
    sys.exit(0)

def client_sender(buffer):
    client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client_sock.connect((target_name, port_number))
        print "[*] Connection built."

        if len(buffer):
            print buffer
            client_sock.send(buffer)
        while True:
            recv_len = 1
            response = ""

            while recv_len:
                data = client_sock.recv(10240)
                recv_len = len(data)
                response += data
                if recv_len < 10240:
                    break
            print response,
            buffer = raw_input("") + "\r\n"

            client_sock.send(buffer)
    except:
        print "[*] Exception! Exiting."
        client_sock.close()

def client_handler(client_sock):
    global isUpload
    global execute_line
    global upload_path
    global isCommand

    if len(upload_path):
        file_buffer = ""
        while True:
            data = client_sock.recv(1024)

            if not data:
                break
            else:
                file_buffer += data

        try:
            file_handler = open(upload_path, "wb")
            file_handler.write(file_buffer)
            file_handler.close()

            client_sock.send("Successfully saved file to %s\r\n" % upload_path)
        except:
            client_sock.send("Failed to save file to %s\r\n" % upload_path)

    if len(execute_line):
        output = run_command(execute_line)
        client_sock.send(output)

    if isCommand:
        while True:
            client_sock.send("NCP->")
            cmd_buffer = ""
            while "\n" not in cmd_buffer:
                cmd_buffer += client_sock.recv(1024)

            response = run_command(cmd_buffer)
            print response

            client_sock.send(response)

def server_loop():
    global target_name

    if not len(target_name):
        target_name = "0.0.0.0"

    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.bind((target_name, port_number))
    server_sock.listen(5)

    while True:
        client_sock, addr = server_sock.accept()
        print "[*] Connection from %s" % str(addr)

        client_thread = threading.Thread(target=client_handler, args=(client_sock,))
        client_thread.start()

def run_command(command):
    print "[*] Received command: %s" % command
    command = command.rstrip()

    try:
        output = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
    except:
        output = "Failed to execute command.\r\n"

    return output


def main():
    global isListen
    global isCommand
    global isUpload
    global execute_line
    global target_name
    global upload_path
    global port_number

    if not len(sys.argv[1:]):
        usage()

    # read the commandline options
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hle:t:p:cu",
                                  ["help", "listen", "execute", "target", "port", "command", "upload"])
    except getopt.GetoptError as err:
        print str(err)
        usage()

    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
        elif o in ("-l", "--listen"):
            isListen = True
        elif o in ("-e", "--execute"):
            execute_line = a
        elif o in ("-c", "--commandshell"):
            isCommand = True
        elif o in ("-u", "--upload"):
            upload_path = a
        elif o in ("-t", "--target"):
            target_name = a
        elif o in ("-p", "--port"):
            port_number = int(a)
        else:
            assert False, "Unhandled Option"

    # are we going to listen or just send data from stdin?
    if not isListen and len(target_name) and port_number > 0:
        buffer = sys.stdin.read()
        client_sender(buffer)
    if isListen:
        server_loop()

main()
