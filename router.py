from socket import socket, timeout, AF_INET, SOCK_DGRAM, SOCK_STREAM
import threading
from sys import argv
import base64
import time

class Router:
    def __init__(self, config_file_name):
        self.ip = self.get_local_ip_address()
        self.port = 9000
        self.router_table = []  # {IP_DEST: x , METRIC: y, IP_EXIT: z}
        self.read_config_file(config_file_name) 

        # Create the UDP socket
        self.UDP_SOCKET = socket(AF_INET, SOCK_DGRAM)
        self.UDP_SOCKET.bind((self.ip, self.port))



    # Read the configuratiion file that matches the name passed as parameter and fill the routing table with the neighbors specified within the file
    def read_config_file(self, config_file_name):
        try:
            with open(config_file_name, 'r') as f:
                for linha in f:
                    table_row_neighbors = linha.strip()
                    if table_row_neighbors:
                       ip_and_metric = table_row_neighbors.split("@")[1]

                       ip_neighbor = ip_and_metric.split("-")[0]
                       metric = ip_and_metric.split("-")[1]

                       self.router_table.append({
                            "IP_DEST": ip_neighbor,
                            "METRIC": metric,
                            "IP_EXIT": ip_neighbor
                       })                         
        except FileNotFoundError:
            print("Arquivo de configuração não encontrado.")


    # Listen to the UDP socket and handle the received messages
    def listen(self):
        while True:
            try:
                data, addr = self.UDP_SOCKET.recvfrom(2048)
                data = data.decode()

                msg_prefix = data[0]
                # * indicates that the router entered in the network
                if(msg_prefix == "*"):
                    ip_new_neighbor = data.split("*")[1]
                    print(f"===== NEW NEIGHBOR ({ip_new_neighbor}) HAS ENTERED NETWORK =====")
                    # RELLY NEED TO ADD IT AGAIN? I THINK NOT ! BECAUSE IT WILL BE ADDED IN THE CONFIG FILE
                    self.router_table.append({
                        "IP_DEST": ip_new_neighbor,
                        "METRIC": 1,
                        "IP_EXIT": ip_new_neighbor
                    })
                elif (msg_prefix == "@"):
                    print("Received route update message")
                    new_routing_table = data
                    print(f"New routing table: {new_routing_table}")
                    # self.getRouterTableDiff(new_routing_table)

            except timeout:
                print("Timeout")
            except Exception as e:
                print(f"Erro ao receber mensagem: {e}")

    def send_table(self):
        while True:
            time.sleep(2)
            self.send_message("@")


    # Send a message to the specified IP address
    def send_message(self, m_type):
        try:

            # * indicates that the router entereed in the network (runs only once)
            if (m_type == "*"):

                # sends a message to all neighbors with '*' and it's own IP address for the neighbors to add it to their routing tables
                message = f"{m_type}{self.ip}"
                print(f"Entering network *: {message}")

                # acho que aqui, não mandamos para IP_DEST, mas sim para para IP_EXIT  !!!!!!!!
                for row in self.router_table:
                    self.UDP_SOCKET.sendto(message.encode(), (row['IP_EXIT'], self.port))


            # @ indicates that it's a route update message
            if(m_type == "@"):
                message = "oi"
                print(f"Updating routing table @: {message}")
                for row in self.router_table:
                    self.UDP_SOCKET.sendto(message.encode(), (row['IP_EXIT'], self.port))

                # como vou adicionar IPs com saida diferente do IP destino !!!!!!!!!!!

                # self.UDP_SOCKET.sendto(message.encode(), (ip, self.port))
        except Exception as e:
            print(f"Erro ao enviar mensagem: {e}")


    # Need to finish this!
    def handle_user_input(self):
        try:
            msg = input().strip()
            # self.send_message("@")
        except KeyboardInterrupt:
            return -1
        print(f"Enviando: {msg}")


    # Print the routing table every 12 seconds, this will run in a thread at the run() method
    def periodic_printRouterTable(self):
        while True:
            time.sleep(5)  # Sleep for 12 seconds
            print("Current routing table (12s):")
            print(self.routingTable_toString())


    # Get the difference between the new routing table and the current routing table
    def getRouterTableDiff(self, new_table):
        # @192.168.1.2-1@192.168.1.3-1
        diff = []
        for row in new_table:
            if row not in self.router_table:
                diff.append(row)



    # AUXILIARY METHODS

    # Get the local IP address, so we doesn't need to ipconfig everytime
    def get_local_ip_address(self):
        try:
            s = socket(AF_INET, SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))  # Conecta a um servidor externo
            ip_local = s.getsockname()[0]  # Obtém o IP local
            s.close()
            return ip_local
        except Exception as e:
            print(f"Erro ao obter IP: {e}")
            return None

    # Return the routing table as a formated string
    def routingTable_toString(self):
        table = "IP_DEST       METRIC   IP_EXIT\n"
        for row in self.router_table:
            table += f"{row['IP_DEST']}   {row['METRIC']}        {row['IP_EXIT']}\n"
        return table

    # Return the size of the routing table
    def routingTable_size(self):
        return len(self.router_table)
    

    # Main router loop
    def run(self):

        # Start the thread that will print the routing table every 12 seconds
        threading.Thread(target=self.periodic_printRouterTable, daemon=True).start()

        # Send the first message to all neighbors, because the router has entered the network
        self.send_message("*")

        # Start the thread that will send for all neighbors the routing table
        threading.Thread(target=self.send_table(), daemon=True).start()

        # Start the thread that will listen to the UDP socket
        threading.Thread(target=self.listen, daemon=True).start()

        # Loop that will handle the user input
        while True:
            if(self.handle_user_input() == -1):
                break


def main():

    try:
        roteador1 = Router('roteadores.txt')
        roteador1.run()
    except timeout:
        print("Timeout")
    except KeyboardInterrupt:
        print("Programa encerrado.")
    

main()
