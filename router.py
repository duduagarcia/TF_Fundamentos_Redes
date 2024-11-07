from socket import socket, timeout, AF_INET, SOCK_DGRAM
import threading
import time

class Router:
    def __init__(self, config_file_name):
        self.ip = self.get_local_ip_address()
        self.port = 9000
        self.router_table = []  # {IP_DEST: x , METRIC: y, IP_EXIT: z}
        self.neighbors = []
        self.last_received_time = []
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
 
                       self.neighbors.append(ip_neighbor)
 
                       self.router_table.append({
                            "IP_DEST": ip_neighbor,
                            "METRIC": metric,
                            "IP_EXIT": ip_neighbor
                       })
 
                       
                       self.last_received_time.append({
                           "IP": ip_neighbor,
                           "TIME": 0
                       })                        
        except FileNotFoundError:
            print("Arquivo de configuração não encontrado.")
 
 
    def tsteTimeout(self):
        while True:
            if(len(self.last_received_time) > 0):
                for row in self.last_received_time:
                    if row['TIME'] >= 35:
                        print(f"Timeout for {row['IP']}")
                        for row1 in self.router_table:
                            if row1['IP_DEST'] == row['IP']:
                                self.router_table.remove(row1)
                                print(f"Removing route to {row1['IP_DEST']}")
                        self.last_received_time.remove(row)
 
                time.sleep(1)
                if(len(self.last_received_time) > 0):
                    for row in self.last_received_time:
                        row['TIME'] += 1
                        # remove for better timeout logs
                        print(f"Handling timeout for {row['IP']} -- {row['TIME']}")
 
           
 
    # Listen to the UDP socket and handle the received messages
    def listen(self):
        while True:
            try:
                data, addr = self.UDP_SOCKET.recvfrom(2048)
                data = data.decode()
 
                # gets the IP address of the sender
                ip_sender = addr[0]
 
 
                print("CHEGOU AQUI")
                for row in self.last_received_time:
                    if row['IP'] == ip_sender:
                        print(f"ACHOU E RESETOU")
                        row['TIME'] = 0
                        break
                # self.last_received_time[ip_sender] = 0
 
 
                # gets the message prefix, to know what to do with the message
                msg_prefix = data[0]
 
 
                # * indicates that the router entered in the network
                if(msg_prefix == "*"):
                    ip_new_neighbor = data.split("*")[1]
                    print("\n")
                    print(f"===== NEW NEIGHBOR ({ip_new_neighbor}) HAS ENTERED NETWORK =====")
                    print("\n")
 
                    if not self.isInsideRoutingTable(ip_new_neighbor):
                        print(f"Adding new neighbor to routing table: {ip_new_neighbor}")
                        self.router_table.append({
                            "IP_DEST": ip_new_neighbor,
                            "METRIC": 1,
                            "IP_EXIT": ip_sender
                        })
 
 
                        self.last_received_time.append({
                            "IP": ip_new_neighbor,
                            "TIME": 0
                        })
 
                elif (msg_prefix == "@"):
                    formatted_table = self.convertTableStringToDict(data)
                    print("\n")
                    print(f"Received route update message from - {ip_sender} \n{formatted_table}")
                    print("\n")
                    print(f"Starting analysis")
                    self.getRouterTableDiff(formatted_table, ip_sender)
                    print("\n")
                elif (msg_prefix == "!"):
                    # "!origem;destino;msg"
                    splitted_data = data.split(";", 3)
                    n_parts = len(splitted_data)
 
                    msg_text = splitted_data[n_parts - 1]
                    ip_final_dest = splitted_data[1]
                    ip_origem = splitted_data[0]
 
 
                    print("\n")
                    print(f"Received message from {ip_sender}: {data}")
                    print("\n")
                    if(ip_final_dest == self.ip):
                        print(f"Message received: {msg_text}")
                    else:
                        print("Não é o destinatário final")
                        new_msg = f"{ip_origem};{ip_final_dest};{msg_text}"
 
                        # for i in range(1, n_parts - 1):
                        #     new_msg += splitted_data[i] + ";"
 
                        # new_msg += msg_text
                        self.send_message("!", new_msg)
 
            except timeout:
                print("Timeout")
            except Exception as e:
                print(f"Erro ao receber mensagem: {e}")
 
    def send_table(self):
        while True:
            time.sleep(15)
            self.send_message("@","")
 
 
    # Send a message to the specified IP address
    def send_message(self, m_type, text):
        try:
 
            # * indicates that the router entereed in the network (runs only once)
            if (m_type == "*"):
 
                message = f"{m_type}{self.ip}"
                print(f"Entering network as: {message}")
                print("Directly connected neighbors: ")
                for row in self.neighbors:
                    print("- " + row)
 
                for row in self.router_table:
                    if(row['IP_DEST'] in self.neighbors):
                       
                        self.UDP_SOCKET.sendto(message.encode(), (row['IP_DEST'], self.port))
            elif (m_type == "@"):
                message = self.convertTableDictToString(self.router_table)
 
                for row in self.router_table:
                    if(row['IP_DEST'] in self.neighbors):
                        print(f"Sending route update message (15s) to {row['IP_DEST']}: {message}" )
                        self.UDP_SOCKET.sendto(message.encode(), (row['IP_DEST'], self.port))
 
            elif (m_type == "!"):
                message = text
                # destination = text.split(";")[0]
                ip_dest = text.split(";", 3)[1]
 
 
                print(f"Sending message to {text}")
                for row in self.router_table:
                    if(row['IP_DEST'] == ip_dest):
                        print(f"Sending message to {ip_dest} through {row['IP_EXIT']}")
                        self.UDP_SOCKET.sendto(message.encode(), (row['IP_EXIT'], self.port))
           
        except Exception as e:
            print(f"Erro ao enviar mensagem: {e}")
 
    def handle_timeout(self):
        while True:
            time.sleep(1)
            print("Handling timeout")
 
 
    # Need to finish this!
    def handle_user_input(self):
        try:
            msg = input().strip()
            self.send_message("!", msg)
        except KeyboardInterrupt:
            return -1
        print(f"Enviando: {msg}")
 
 
    def periodic_printRouterTable(self):
        while True:
            time.sleep(12)  # Sleep for 12 seconds
            print("\n")
            print("Current routing table (12s):")
            print(self.routingTable_toString())
            print("\n")
 
 
    # Get the difference between the new routing table and the current routing table
    def getRouterTableDiff(self, new_table, ip_sender):
 
        old_table = self.router_table.copy()
 
        for row in new_table:
            ip_dest = row['IP_DEST']
            metric = row['METRIC']
            ip_exit = ip_sender
 
            if self.ip != ip_dest:
 
                # If the IP destination is not in the routing table, add it
                if self.isInsideRoutingTable(ip_dest) == False:
                    print(f"Adding new route to routing table: {ip_dest}")
                    self.router_table.append({
                        "IP_DEST": ip_dest,
                        "METRIC": int(metric) + 1,
                        "IP_EXIT": ip_exit
                    })
                else:
                    # If the IP destination is in the routing table, but the metric is different, update it
                    for row in self.router_table:
                        if row['IP_DEST'] == ip_dest:
 
                            if int(metric) + 1 < int(row['METRIC']):
                                print(f"Updating route metric in routing table: {ip_dest}")
                                row['METRIC'] = int(metric) + 1
                                row['IP_EXIT'] = ip_exit
 
        if(old_table != self.router_table):
            print("Routing table has changed")
        else:
            print("Routing table has not changed")
 
 
    # AUXILIARY METHODS
 
    def get_local_ip_address(self):
        try:
            s = socket(AF_INET, SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip_local = s.getsockname()[0]
            s.close()
            return ip_local
        except Exception as e:
            print(f"Erro ao obter IP: {e}")
            return None
 
 
    def routingTable_toString(self):
        table = "IP_DEST           METRIC   IP_EXIT\n"
        for row in self.router_table:
            table += f"{row['IP_DEST']}   {row['METRIC']}        {row['IP_EXIT']}\n"
        return table
 
   
    def routingTable_size(self):
        return len(self.router_table)
   
   
    def isInsideRoutingTable(self, ip):
        for row in self.router_table:
            if row['IP_DEST'] == ip:
                return True
        return False
   
   
    def convertTableStringToDict(self, table_string):
        # @192.168.1.2-1@192.168.1.3-1
        rows = table_string.split("@")
 
        table = []
 
        for row in rows:
            if row:
                ip_and_metric = row.split("-")
                ip = ip_and_metric[0]
                metric = ip_and_metric[1]
 
                table.append({
                    "IP_DEST": ip,
                    "METRIC": metric,
                    "IP_EXIT": ip
                })
       
        return table
   
    def convertTableDictToString(self, table):
        table_string = ""
        for row in table:
            table_string += f"@{row['IP_DEST']}-{row['METRIC']}"
        return table_string
 
 
    def run(self):
 
        # PRINT ROUTER TABLE FOR USER (12s)
        threading.Thread(target=self.periodic_printRouterTable, daemon=True).start()
 
        self.send_message("*", "")
 
        # SEND TABLE TO NEIGHBORS (15s)
        threading.Thread(target=self.send_table, daemon=True).start()
 
        # LISTEN UDP
        threading.Thread(target=self.listen, daemon=True).start()
 
        # TIMEOUT
        threading.Thread(target=self.tsteTimeout, daemon=True).start()
 
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