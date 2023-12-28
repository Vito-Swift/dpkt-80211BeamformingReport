# dpkt with 802.11 Beamforming Report Extension

Modification Path: (dpkt/ieee80211NDP.py)

## How to install:

```shell
pip3 install -e .
```

## How to test:

Move to `examples/print_80211_ActionNoACK.py`, we have implemented a test program to read a traffic trace in 
`examples/data/rtl8814.pcap`. The main program looks like this:

```python
if __name__ == '__main__':
    dirname = os.path.dirname(__file__)
    traffic_trace = os.path.join(dirname, 'data/rtl8814.pcap')
    timestamp, params, Vs, ASNRs =
        read_beamforming_report(traffic_trace, beamformer_mac=b'\xe8\x4e\x06\x95\x28\xcd', max_num=2)

    np.set_printoptions(threshold=10)
    
    print(f"Numer of records: {timestamp.shape[0]}")
    for i in range(timestamp.shape[0]):
        print(f"i-th V: {Vs[i]}")
        print(f"i-th ASNR: {ASNRs[i]}")
```

After running this code, you can read the **top-2** beamforming report in the entire traffic trace. The result will 
looks like:

```shell
> python3 examples/print_80211_ActionNoAck.py

Numer of records: 2
i-th V: [[[ 0.85669544-0.04208675j -0.51348348+0.02522583j]
  [ 0.51410274+0.j          0.85772861+0.j        ]]

 [[ 0.84844499-0.12585493j -0.50853836+0.07543454j]
  [ 0.51410274+0.j          0.85772861+0.j        ]]

 [[ 0.85669544-0.04208675j -0.51348348+0.02522583j]
  [ 0.51410274+0.j          0.85772861+0.j        ]]

 ...

 [[ 0.09853816+0.66429034j -0.10872011-0.73293145j]
  [ 0.74095113+0.j          0.67155895+0.j        ]]

 [[ 0.09853816+0.66429034j -0.10872011-0.73293145j]
  [ 0.74095113+0.j          0.67155895+0.j        ]]

 [[ 0.10872011+0.73293145j -0.09853816-0.66429034j]
  [ 0.67155895+0.j          0.74095113+0.j        ]]]
i-th ASNR: [39.5  33.25]
i-th V: [[[ 0.80224003+0.03941153j -0.59498176-0.02922958j]
  [ 0.5956993 +0.j          0.80320753+0.j        ]]

 [[ 0.85669544-0.04208675j -0.51348348+0.02522583j]
  [ 0.51410274+0.j          0.85772861+0.j        ]]

 [[ 0.84844499-0.12585493j -0.50853836+0.07543454j]
  [ 0.51410274+0.j          0.85772861+0.j        ]]

 ...

 [[ 0.16317552+0.65143317j -0.18003644-0.71874575j]
  [ 0.74095113+0.j          0.67155895+0.j        ]]

 [[ 0.18003644+0.71874575j -0.16317552-0.65143317j]
  [ 0.67155895+0.j          0.74095113+0.j        ]]

 [[ 0.14474312+0.57784694j -0.19516351-0.77913641j]
  [ 0.80320753+0.j          0.5956993 +0.j        ]]]
i-th ASNR: [41.25 34.75]

```



