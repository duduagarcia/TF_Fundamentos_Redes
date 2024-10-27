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
        self.UDP_SOCKET = socket(AF_INET, SOCK_DGRAM)
        self.UDP_SOCKET.bind((self.ip, self.port))

        # Iniciar as threads para enviar e receber mensalmente
        # threading.Thread(target=self.receive_messages, daemon=True).start()
        # threading.Thread(target=self.send_messages, daemon=True).start()

        # threading.Thread(target=self.listen, args=(self.CONTROLL_SOCKET,)).start()
        # threading.Thread(target=self.listen, args=(self.DATA_SOCKET,)).start()



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
    # def listen(self):
    #     while True:
    #         try:
    #             data, addr = self.UDP_SOCKET.recvfrom(1024)
    #             print(f"Recebi: {data}")
    #         except timeout:
    #             print("Timeout")
    #         except Exception as e:
    #             print(f"Erro ao receber mensagem: {e}")

    # # Send a message to the specified IP address
    # def send_message(self, ip, message):
    #     try:
    #         self.UDP_SOCKET.sendto(message.encode(), (ip, self.port))
    #     except Exception as e:
    #         print(f"Erro ao enviar mensagem: {e}")


    def handle_user_input(self):
        try:
            msg = input().strip()
        except KeyboardInterrupt:
            return -1
        print(f"Enviando: {msg}")


    # Print the routing table every 12 seconds, this will run in a thread at the run() method
    def periodic_printRouterTable(self):
        while True:
            time.sleep(12)  # Sleep for 12 seconds
            print("Current routing table (12s):")
            print(self.routingTable_toString())



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
        threading.Thread(target=self.periodic_printRouterTable, daemon=True).start()

        while True:
            if(self.handle_user_input() == -1):
                break


def main():
    print("Hello, World!")

    try:
        roteador1 = Router('roteadores.txt')
        roteador1.run()
    except timeout:
        print("Timeout")
    except KeyboardInterrupt:
        print("Programa encerrado.")
    

main()
