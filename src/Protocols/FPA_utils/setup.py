from Crypto.Util import number
import time
from ecdsa.curves import *
from src.utils.node import *


def bid_decomposition(self):
    bits = [int(digit) for digit in bin(self.bid)[2:]]

    numtoprepend = 32 - len(bits)
    for i in range(numtoprepend):
        bits.insert(0, 0)

    for bit in bits:
        self.bits.append(bit)
        self.bit_commitments.append(self.pd.commit(bit))


def setup(self):
    # Stage 1
    # change (secret)
    change = 0.1
    # fee: work
    work = 0.1
    # build secret deposit
    bid_param = {
        "bid": self.bid,
        "change": change,
        "work": work
    }

    # (a) send to smart contract (BroadcastNode)
    self.send_to_node(self.bc_node, (bid_param))  # Not a dict
    # (b) compute bit commitments
    bid_decomposition(self)

    # (c) build UTXO for confidential transaction - skippable
    # (d) compute r_out, we think it's for range proof - skippable
    # (e) Uses stuff from C - SKIP
    # (f) Compute shares of g^bi and h^rbi, Use distribution from PVSS protocol with committee - skippable?
    # (g) ?
    # (h) ?
    # (i) ?
    # secret_key =

    self.contractparams = get_message(self.bc_node)

    self.p = self.contractparams["p"]
    self.h = Point(self.contractparams["h"]["x"],
                   self.contractparams["h"]["y"], self.pd.cp)
    self.g = Point(self.contractparams["g"]["x"],
                   self.contractparams["g"]["y"], self.pd.cp)

    # Stage 2: Compute all big X's and send commits along with X to other nodes. Is used for stage three in veto
    commit_x_dict = {}
    for i in range(len(self.bit_commitments)):
        x = number.getRandomRange(1, self.p - 1)
        self.small_xs.append(x)

        big_x = self.pd.cp.mul_point(x, self.g)

        temp_dict = {
            "commit": {
                "x": self.bit_commitments[i][0].x,
                "y": self.bit_commitments[i][0].y
            },
            "big_x": {
                "x": big_x.x,
                "y": big_x.y
            }
        }
        commit_x_dict[i] = temp_dict

    reset_all_node_msgs(self.all_nodes)

    commits_w_index = {
        "client_index": int(self.index),
        "commit_x": commit_x_dict
    }

    # maybe also send identification of yourself along ?
    self.send_to_nodes(
        (commits_w_index), exclude=[self.bc_node])

    for i in range(len(self.clients) + 1):
        self.commitments.append([])  # add room for another client
        self.big_xs.append([])  # add room for another client

    time.sleep(0.2)

    commit_and_X_arr = get_all_messages_arr(self, len(self.clients))

    unpack_commitments_x(self, [commits_w_index])
    unpack_commitments_x_arr(self, commit_and_X_arr)

    time.sleep(0.2)

    # unpack_commitment_and_x(self, commit_and_X_array)

    # TODO: Stage 3 of setup we now send the array containing commitments and big X's maybe make a helper method to unravel it again
    try:
        for i in range(len(self.big_xs)):
            self.big_ys.append([])
            for j in range(len(self.big_xs[0])):
                left_side = self.pd.param[1]
                right_side = self.pd.param[1]

                for h in range(self.index):  # Left side of equation
                    left_side = self.pd.cp.add_point(
                        left_side, self.big_xs[h][j])

                for h in range(self.index+1, len(self.big_xs)):  # Right side of equation
                    right_side = self.pd.cp.add_point(
                        right_side, self.big_xs[h][j])

                self.big_ys[i].append(self.pd.cp.sub_point(
                    left_side, right_side))
    except:
        print(
            f"Failed when creating Y's for {self.id} - Big X's: {len(self.big_xs)}")
    # verify c_j for each other party p_j, skipped atm
