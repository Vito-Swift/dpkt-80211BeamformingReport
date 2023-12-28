# $Id: 80211NDP.py 53 2022-01-08 01:22:57Z Vito-Swift $
# -*- coding: utf-8 -*-
"""IEEE 802.11 VHT/HE Null Data Packet Sounding Protocol"""
from __future__ import print_function
from __future__ import absolute_import

from . import dpkt
import math
from .compat import ntole

C_VHT = 0x15
C_HE = 0x1e

angle_representation_table = [
    [2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # 2 x 1
    [2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # 2 x 2
    [2, 2, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0],  # 3 x 1
    [2, 2, 1, 1, 2, 1, 0, 0, 0, 0, 0, 0],  # 3 x 2
    [2, 2, 1, 1, 2, 1, 0, 0, 0, 0, 0, 0],  # 3 x 3
    [2, 2, 2, 1, 1, 1, 0, 0, 0, 0, 0, 0],  # 4 x 1
    [2, 2, 2, 1, 1, 1, 2, 2, 1, 1, 0, 0],  # 4 x 2
    [2, 2, 2, 1, 1, 1, 2, 2, 1, 1, 2, 1],  # 4 x 3
    [2, 2, 2, 1, 1, 1, 2, 2, 1, 1, 2, 1],  # 4 x 4
]
angle_psi_val = 0x1
angle_phi_val = 0x2


def signbit_convert(data, maxbit):
    if data & (1 << (maxbit - 1)):
        data -= (1 << maxbit)
    return data


class IEEE80211NDP(dpkt.Packet):
    __hdr__ = (
        ('category', 'B', 0x0),  # Category code, i.e. VHT=0x15
        ('action', 'B', 0x0),  # Action code, i.e. VHTCompressedBeamforming=0
    )

    def __init__(self, *args, **kwargs):
        super(IEEE80211NDP, self).__init__(*args, **kwargs)

    def unpack(self, buf):
        dpkt.Packet.unpack(self, buf)
        self.data = buf[self.__hdr_len__:]

        decoder = {
            C_VHT: ('VHT', self.VHTMIMOControl),
            C_HE: ('HE', self.HEMIMOControl),
        }
        try:
            parser = decoder[self.category][1]
            name = decoder[self.category][0]
        except KeyError:
            raise dpkt.UnpackError("KeyError: category=%s" % self.category)

        field = parser(self.data)
        setattr(self, name, field)

        self.data = field.data

    class VHTMIMOControl(dpkt.Packet):
        """802.11ac MIMO Control Decoder (Report.category=0x15)"""
        __hdr__ = (
            ('_vht_mimo_ctrl_1', 'B', 0),
            ('_vht_mimo_ctrl_2', 'B', 0),
            ('_vht_mimo_ctrl_3', 'B', 0),
        )
        __bit_fields__ = {
            '_vht_mimo_ctrl_1': (
                ('bw', 2),  # Channel bandwidth, 2 bits
                ('nr', 3),  # Number of rows, 3 bits
                ('nc', 3),  # Number of columns, 3 bits
            ),
            '_vht_mimo_ctrl_2': (
                ('ffs', 1),  # First feedback segment, 1 bit
                ('rm', 3),  # Remaining feedback segments, 3 bits
                ('fb', 1),  # Feedback type, 1 bit
                ('codebook', 1),  # Codebook information, 1 bit
                ('ng', 2),  # Grouping, 2 bits
            ),
            '_vht_mimo_ctrl_3': (
                ('sounding_token', 6),  # Sounding dialog token number, 6 bits
                ('rs', 2),  # Reserved, 2 bits
            )
        }

        @property
        def num_cols(self):
            """Number of columns (equiv.., number of Space-Time Streams)"""
            return self.nc + 1

        @property
        def num_rows(self):
            """Number of rows (equiv.., number of TX antennas)"""
            return self.nr + 1

        @property
        def num_subcarriers(self):
            """Number of subcarriers"""
            ns_codebook = {
                # Bandwidth
                20: {0: 52, 1: 30, 2: 16},
                40: {0: 108, 1: 58, 2: 30},
                80: {0: 234, 1: 122, 2: 62},
                160: {0: 468, 2: 244, 1: 124},
            }

            return ns_codebook[self.channel_bandwidth][self.ng]

        @property
        def channel_bandwidth(self):
            """Channel bandwidth (in MHz)"""
            bw_codebook = {
                0x0: 20,
                0x1: 40,
                0x2: 80,
                0x3: 160
            }

            return bw_codebook[self.bw]

        @property
        def phi_size(self):
            """Size of angle phi (in bits)"""
            phi_codebook = {
                # SU-MIMO
                0: {0: 4, 1: 6},
                # MU-MIMO
                1: {0: 7, 1: 9},
            }

            return phi_codebook[self.fb][self.codebook]

        @property
        def psi_size(self):
            """Size of angle psi (in bits)"""
            psi_codebook = {
                # SU-MIMO
                0: {0: 2, 1: 4},
                # MU-MIMO
                1: {0: 5, 1: 7},
            }
            return psi_codebook[self.fb][self.codebook]

        @property
        def num_angles(self):
            """Number of angles"""
            if self.num_rows == 0x2:
                return 0x2
            na_codebook = {
                # nr
                0x3: {0x1: 0x4, 0x2: 0x6, 0x3: 0x6},  # nc
                0x4: {0x1: 0x6, 0x2: 0xa, 0x3: 0xc, 0x4: 0xc},  # nc
            }
            return na_codebook[self.num_rows][self.num_cols]

        def print_elem_fields(self):
            print("num cols: {} ({})".format(self.nc, bin(self.nc)[2:]))
            print("num rows: {} ({})".format(self.nr, bin(self.nr)[2:]))
            print("chan width: {} ({})".format(self.bw, bin(self.bw)[2:]))
            print("grouping: {} ({})".format(self.ng, bin(self.ng)[2:]))
            print("codebook: {} ({})".format(self.codebook, bin(self.codebook)[2:]))
            print("feedback: {} ({})".format(self.fb, bin(self.fb)[2:]))
            print("remaining: {} ({})".format(self.rm, bin(self.rm)[2:]))
            print("ffs: {} ({})".format(self.ffs, bin(self.ffs)[2:]))
            print("rs: {} ({})".format(self.rs, bin(self.rs)[2:]))
            print("sdt: {} ({})".format(self.sounding_token, bin(self.sounding_token)[2:]))

        def decode_psi(self, val, size):
            return (val * math.pi / float(1 << (size + 1))) + (math.pi / float(1 << (size + 2)))

        def decode_phi(self, val, size):
            return (val * math.pi / float(1 << (size - 1))) + (math.pi / float(1 << size))

        @property
        def V_matrix(self):
            pass

        def unpack(self, buf):
            dpkt.Packet.unpack(self, buf)
            self.data = buf[self.__hdr_len__:]

            # self.print_elem_fields()

            # parse ASNR field
            def asnr_parse(asnr):
                if asnr > 128:
                    asnr -= 256
                return -10.0 + (asnr + 128) * 0.25

            self.asnr = [asnr_parse(self.data[i]) for i in range(self.num_cols)]
            # parse compressed beamforming matrix
            self.angles = [[] for i in range(self.num_subcarriers)]

            phi_size = self.phi_size
            psi_size = self.psi_size
            phi_mask = (1 << phi_size) - 1
            psi_mask = (1 << psi_size) - 1

            # read 2 bytes (16 bits) a single time
            self.data += b"\x00"  # add 1 byte padding in the tail so as to prevent element fetch out of range
            idx = self.num_cols
            elem = self.data[idx]
            idx += 1
            elem += (self.data[idx] << 8)
            idx += 1

            bits_left = 16
            current_data = elem & ((1 << 16) - 1)
            angle_rp_idx = int(((2 + self.num_cols) * (self.num_cols - 2) / 2) + self.num_rows - 1)

            for k in range(self.num_subcarriers):
                for angle_idx in range(self.num_angles):
                    if angle_representation_table[angle_rp_idx][angle_idx] == angle_psi_val:
                        # parse angle psi
                        if bits_left - psi_size < 0:
                            elem = self.data[idx]
                            idx += 1
                            elem += (self.data[idx] << 8)
                            idx += 1
                            current_data += elem << bits_left
                            bits_left += 16
                        val = current_data & psi_mask
                        self.angles[k].append(self.decode_psi(val, psi_size))

                        bits_left -= psi_size
                        current_data = current_data >> psi_size

                    elif angle_representation_table[angle_rp_idx][angle_idx] == angle_phi_val:
                        # parse angle phi
                        if bits_left - phi_size < 0:
                            elem = self.data[idx]
                            idx += 1
                            elem += (self.data[idx] << 8)
                            idx += 1
                            current_data += elem << bits_left
                            bits_left += 16
                        val = current_data & phi_mask
                        self.angles[k].append(self.decode_phi(val, phi_size))

                        bits_left -= phi_size
                        current_data = current_data >> phi_size

            self.data = self.data[:-1]

    class HEMIMOControl(dpkt.Packet):
        """802.11ax MIMO Control Decoder (Report.category=0x1e)"""
        # TODO: to be implemented
