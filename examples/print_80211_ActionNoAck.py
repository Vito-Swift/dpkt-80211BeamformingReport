from scipy.constants import c, pi
from math import sin, e, atan
import numpy as np
import os
import time
import sys
import dpkt


def decode_beamforming_matrix(angles, nsubc, nrows, ncols):
    iternum = min(ncols, nrows - 1)
    # pre-compute the D matrices
    init = np.transpose(np.repeat(np.eye(nrows, dtype=complex)[:, :, np.newaxis], nsubc, axis=2), (2, 0, 1))
    mask = np.transpose(np.repeat(np.eye(nrows, ncols, dtype=complex)[:, :, np.newaxis], nsubc, axis=2), (2, 0, 1))
    res = np.copy(init)
    offset = 0
    for i in range(1, iternum + 1):
        D = np.e ** (1j * angles[:, offset:offset + nrows - i])
        offset = offset + nrows - i
        D = np.pad(D,
                   ((0, 0), (i - 1, 1)),
                   'constant',
                   constant_values=(1, 1))  # padding i-1 1 before and a 1 after the sequence
        D = np.eye(nrows) * D[:, np.newaxis, :]  # diagonalize the D vector for each matrix
        res = res @ D
        for l in range(i + 1, nrows + 1):
            G = np.copy(init)
            psi = angles[:, offset]
            G[:, i - 1, i - 1] = np.cos(psi)
            G[:, l - 1, i - 1] = np.sin(psi)
            G[:, i - 1, l - 1] = -np.sin(psi)
            G[:, l - 1, l - 1] = np.cos(psi)
            res = res @ G
            offset += 1

    return res @ mask


def V_sort(V):
    # time alignment
    for pkt_V in V:
        last_angle = np.angle(pkt_V[0, :])

    # frequency alignment
    # V: shape[num_sc,num_ant,num_ant]
    num_sc = V.shape[1]
    num_ant = V.shape[2]

    for pkt_V in V:
        for t in range(1, num_sc):
            for i in range(num_ant):
                pass
    return V


def read_beamforming_report(filename, beamformer_mac, max_num=10000):
    all_angles = []
    asnr = []
    timestamp = []
    nrows = 0
    ncols = 0
    nsubc = 0
    for ts, pkt in dpkt.pcap.Reader(open(filename, 'rb')):
        try:
            rad = dpkt.radiotap.Radiotap(pkt)
            frame = rad.data
            nsubc = frame.action_no_ack.VHT.num_subcarriers
            nrows = frame.action_no_ack.VHT.num_rows
            ncols = frame.action_no_ack.VHT.num_cols
            if frame.type == 0 and frame.subtype == 14:
                if frame.mgmt.dst == beamformer_mac:
                    timestamp.append(ts)
                    asnr.append(frame.action_no_ack.VHT.asnr)
                    all_angles.append(frame.action_no_ack.VHT.angles)
                    if len(timestamp) >= max_num:
                        break
        except Exception as e:
            pass

    V = np.zeros((len(all_angles), nsubc, nrows, ncols), dtype=complex)
    for idx, sndpkt in enumerate(all_angles):
        angles = np.array(sndpkt)
        V[idx, :, :, :] = decode_beamforming_matrix(angles, nsubc, nrows, ncols)

    return np.array(timestamp), (nsubc, nrows, ncols), V, np.array(asnr)


if __name__ == '__main__':
    dirname = os.path.dirname(__file__)
    traffic_trace = os.path.join(dirname, 'data/rtl8814.pcap')
    timestamp, params, Vs, ASNRs = \
        read_beamforming_report(traffic_trace, beamformer_mac=b'\xe8\x4e\x06\x95\x28\xcd', max_num=2)

    np.set_printoptions(threshold=10)

    print(f"Numer of records: {timestamp.shape[0]}")
    for i in range(timestamp.shape[0]):
        print(f"i-th V: {Vs[i]}")
        print(f"i-th ASNR: {ASNRs[i]}")
