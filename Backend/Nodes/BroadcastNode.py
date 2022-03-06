from Backend.Nodes.FastNode import FastNode

class BroadcastNode (FastNode):              
    def run(self):
        while not self.terminate_flag.is_set():
            connection, client_address = self.sock.accept()

            connected_node_id = self.exchange_id(connection)

            connected_node_msg = connection.recv(4096).decode('utf-8')
            print(connected_node_msg)

            self.start_thread_connection(connection, connected_node_id, client_address)

            self.connections.append(connected_node_msg)

            if len(self.connections) == 3:
                break

        self.send_to_nodes(str(self.connections))
    
        print("Broadcast Finished")
