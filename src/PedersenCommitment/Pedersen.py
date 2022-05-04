from ecpy.curves import Curve
from Crypto.Util import number


class Pedersen:
    def __init__(self):
        self.cp = Curve.get_curve("secp256k1")

        self.param = self.setup()

    def setup(self):
        # 2^256
        size = 2**self.cp.size

        # Order of the group to sample Z_p from
        p = self.cp.order

        # Generator of group
        g = self.cp.generator

        # Random scalar from G (Blinding factor)
        r = number.getRandomRange(1, size) % p

        # How the fuck is this possible? g is generator and r is integer?
        h = self.cp.mul_point(r, g)

        return p, g, h

    def create_commit(self, param, m, r):
        g, h = param

        # Create to scalar points on the curve
        mg = self.cp.mul_point(m, g)
        rh = self.cp.mul_point(r, h)

        # Commitment which is the two points on the curve
        c = self.cp.add_point(mg, rh)

        return c, r

    def commit(self, param, m):
        p, g, h = param

        # Randomness of Z_p
        r = number.getRandomRange(1, p-1)

        c, _ = self.create_commit((g, h), m, r)

        return c, r

    def open(self, param, m, c, r):
        _, g, h = param

        o, _ = self.create_commit((g, h), m, r)

        # Check if the commitment is valid
        if o == c:
            return True
        else:
            return False
