from functools import partial

import torch

from se3cnn.non_linearities.gated_block import GatedBlock
from se3cnn.non_linearities.rescaled_act import relu, sigmoid, tanh, absolute
from se3cnn.non_linearities.gated_block_parity import GatedBlockParity
from se3cnn.point.kernel import Kernel
from se3cnn.point.operations import Convolution
from se3cnn.point.radial import ConstantRadialModel
from se3cnn.SO3 import normalizeRs, rep, rot


class RandomDataRotation(object):
    def __init__(self, batch, n_atoms, Rs_in, Rs_out):
        self.abc = torch.randn(3)  # Rotation seed of euler angles.
        self.rot_geo = rot(*self.abc)
        self.D_in = rep(Rs_in, *self.abc)
        self.D_out = rep(Rs_out, *self.abc)

        c = sum([mul * (2 * l + 1) for mul, l, _ in Rs_in])
        self.feat = torch.randn(batch, n_atoms, c)  # Transforms with wigner D matrix
        self.geo = torch.randn(batch, n_atoms, 3)  # Transforms with rotation matrix.


def check_rotation(batch: int = 10, n_atoms: int = 25):
    # Setup the network.
    K = partial(Kernel, RadialModel=ConstantRadialModel)
    C = partial(Convolution, K)
    Rs_in = [(1, 0), (1, 1)]
    Rs_out = [(1, 0), (1, 1), (1, 2)]
    m = GatedBlock(
        Rs_in,
        Rs_out,
        scalar_activation=sigmoid,
        gate_activation=sigmoid,
        Operation=C
    )

    # Setup the data. The geometry, input features, and output features must all rotate.
    abc = torch.randn(3)  # Rotation seed of euler angles.
    rot_geo = rot(*abc)
    D_in = rep(Rs_in, *abc)
    D_out = rep(Rs_out, *abc)

    c = sum([mul * (2 * l + 1) for mul, l in Rs_in])
    feat = torch.randn(batch, n_atoms, c)  # Transforms with wigner D matrix
    geo = torch.randn(batch, n_atoms, 3)  # Transforms with rotation matrix.

    # Test equivariance.
    F = m(feat, geo)
    RF = torch.einsum("ij,zkj->zki", D_out, F)
    FR = m(feat @ D_in.t(), geo @ rot_geo.t())
    return (RF - FR).norm() < 10e-5 * RF.norm()


def check_rotation_parity(batch: int = 10, n_atoms: int = 25):
    # Setup the network.
    K = partial(Kernel, RadialModel=ConstantRadialModel)
    C = partial(Convolution, K)
    Rs_in = [(1, 0, 1)]
    m = GatedBlockParity(
        Operation=C,
        Rs_in=Rs_in,
        Rs_scalars=[(4, 0, 1)],
        act_scalars=[(-1, relu)],
        Rs_gates=[(8, 0, 1)],
        act_gates=[(-1, sigmoid)],
        Rs_nonscalars=[(4, 1, -1), (4, 2, 1)]
    )
    Rs_out = m.Rs_out

    # Setup the data. The geometry, input features, and output features must all rotate.

    raise NotImplementedError


if __name__ == '__main__':
    check_rotation()
    # check_rotation_parity()
