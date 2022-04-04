from Infrastructure.Nodes.FastNode import FastNode
from Infrastructure.PedersenCommit.Pedersen import Pedersen

import threading
import time
from ecdsa import SigningKey, SECP256k1 #Bitcoin curve
import random 
import math
from fractions import Fraction
import functools

class ClientNode (FastNode): 
    def __init__(self, host, port, bid, id=None, callback=None, max_connections=0):
        super(ClientNode, self).__init__(host, port, id, callback, max_connections)
        
        self.debugPrint = False
        self.easy_signatures = True
        self.bid = bid
        
        self.sk = SigningKey.generate()
        self.vk = self.sk.verifying_key
        
        self.pd = Pedersen(10)
        self.bit_commitments = []
        
        self.broadcast_node = None
        self.vetoarray= []

        self.contractparams = None

            
    def get_trimmed_info(self, node_info=str):
        try:
            info_array = []
            
            remove_braces = node_info.strip("[]")
            temp_info = remove_braces.split(" ")
            for info in temp_info:
                remove_commas = info.strip(',')
                remove_ticks = remove_commas.strip("'")
                host, port = remove_ticks.split(":")
                
                converted_port = int(port)
                
                info_tuple = (host, converted_port)
                info_array.append(info_tuple)
                
            return info_array  
        except:
            print(f"{self.id} has crashed when splitting node_info")
            self.sock.close()     
    
    def bid_decomposition(self):
        bits = [int(digit) for digit in bin(self.bid)[2:]]
        
        numtoprepend = 32  - len(bits)        
        for i in range(numtoprepend):
            bits.insert(0, 0)
        
        for bit in bits:
            self.bit_commitments.append(self.pd.p.commit(self.pd.param, bit))
        
        if self.debugPrint:
            print(f"Bit commits for {self.id}: {str(self.bit_commitments)}")
            
        # for i in range(len(self.bit_commitments)):
        #     print(f"{str(self.bit_commitments[i][0])} open val {self.pd.v.openBool(self.pd.param, self.bit_commitments[i][0], bits[i], self.bit_commitments[i][1])}")
    
    def connect_to_clients(self, node_info):
        try:
            host = node_info[0]
            port = int(node_info[1])
            
            if not(host == self.host and port == self.port): 
                self.clients.append((host, port))     
                self.connect_with_node(host, port)   
        except:
            print(f"{self.id} has crashed when connecting to clients")
            self.sock.close()             
                
    def connect_to_nodes(self):
        try:
            self.connect_with_node(self.broadcast_host, self.broadcast_port)
            
            node_info = f"{self.host}:{str(self.port)}"
            self.send_to_nodes(node_info)

            while self.all_nodes[0].get_node_message() == "":
                time.sleep(0.1)
            
            node_info = self.all_nodes[0].get_node_message()
            self.all_nodes[0].reset_node_message()
                    
            trimmed_info = self.get_trimmed_info(node_info)
            
            self.broadcast_node = self.all_nodes[0]
            
            # self.disconnect_with_node(self.all_nodes[0])
            # self.nodes_outbound.remove(self.all_nodes[0])
               
            time.sleep(0.1)
                    
            for node in trimmed_info:
                self.connect_to_clients(node)
                time.sleep(0.1)
        except:
            print(f"{self.id} has crashed when connecting to all nodes")
            self.sock.close()
            
    def get_conflicting_messages(self):
        pass
         
    def get_message(self, node):
        while node.get_node_message() == "":
            time.sleep(0.1)

        msg = node.get_node_message()
        node.reset_node_message()

        time.sleep(0.1)

        return msg

    def get_all_messages(self, num_messages):
        while len(self.messages) != num_messages:
            for node in self.all_nodes:
                msg = node.get_node_message()
                
                if msg != "":
                    self.messages.append(msg)
                    node.reset_node_message()
                time.sleep(0.05)

    def get_all_messages_arr(self, num_messages): # we get stuck here when there is no msg
        messages = []

        while len(messages) != num_messages:
            for node in self.all_nodes:
                msg = node.get_node_message()
                if msg != "":
                    messages.append(msg)
                    node.reset_node_message()
                time.sleep(0.05)
        
        return messages

    def reset_all_node_msgs(self):
        for node in self.all_nodes:
            node.reset_node_message()

    def get_broadcast_node(self):
        for x in self.all_nodes:
            if "Broadcast" in str(x):
                return x

    def setup(self):
        #Broadcast node
        bc_node = self.get_broadcast_node()
        # change (secret)
        change = 0.1  
        # fee: work
        work = 0.1
        # build secret deposit 
        param = F"{self.bid};{change};{work}"
        [self.bid, change, work, self.id]
        g = None # receive from smart contract, everyone gets same g + h
        h = None # receive from smart contract, everyone gets same g + h 


        # (a) send to smart contract (BroadcastNode)
        self.send_to_nodes(param, exclude=[self.clients])
        # (b) compute bit commitments
        self.bid_decomposition()
        # (c) build UTXO for confidential transaction - skippable
        # (d) compute r_out, we think it's for range proof - skippable
        # (e) Uses stuff from C - SKIP
        # (f) Compute shares of g^bi and h^rbi, Use distribution from PVSS protocol with committee - skippable?
        # (g) ?
        # (h) ? 
        # (i) ? 
        # secret_key = 
        
        self.contractparams = self.get_message(bc_node).split(";")

        print(f"THIS IS THE MSG {self.contractparams}")

    def prod(vec):
        return functools.reduce(lambda a, b: a*b, vec, 1)

    def veto(self):
        q = int(self.contractparams[6])
        g = int(self.contractparams[4])

        self.get_all_messages(len(self.clients))
        time.sleep(0.1)

        for j in range(len(self.bit_commitments)): # Rounds
            # print("\nRound " + str(j))
            
            # compute the random value x and broadcast that to all other nodes
            # get random value from the field. 
            # Random elements of Z_q used for commitments
            x = random.randint(1,q - 1)

            self.send_to_nodes(str(x), exclude=[self.get_broadcast_node()])

            time.sleep(0.1)

            x_r_array = self.get_all_messages_arr(len(self.clients))

            time.sleep(0.1)
 
            
            final_x = 1

            for x in x_r_array:
                print("in xr array")
                new_x = int(x)
                final_x = final_x * (-new_x)

            y = g**final_x
            print(f"{self.id}: {y} round: {j}")

            # time.sleep(0.5)
                #print(f"This is messages for p{self.id} {len(messages)}")
                #Time to compute either yi or rhat

                #Y_i:
                #Y = Fraction(self.prod(xk) , self.prod(xk))
            
        
    def run(self):
        accept_connections_thread = threading.Thread(target=self.accept_connections)
        accept_connections_thread.start()
        
        self.connect_to_nodes()        
        
        # print(f"Nodes for {self.id}: {str(self.all_nodes)}")
        
        self.setup()
        self.veto()
