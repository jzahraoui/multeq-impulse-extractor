#!/usr/bin/python3

from array import ArrayType
import json
import sys
import os

def main():
    header = """* Impulse Response data saved by REW
* IR is not normalised
* IR window has not been applied
* IR is not the min phase version
* Excitation: Imported Impulse Response, 48000.0 Hz sampling
* Response measured over: 2,9 to 24 000,0 Hz
0 // Peak value before normalisation
0 // Peak index
16384 // Response length
2.0833333333333333E-5 // Sample interval (seconds)
0.0 // Start time (seconds)
* Data start"""

    in_file = sys.argv[1]
    in_file_wo_ext = os.path.splitext(in_file)[0]
    in_json = json.load(open(in_file, 'r'))
    channels = dict((item['commandId'], item) for item in in_json['detectedChannels'])
    for speaker, channel in channels.items():
        for measurement, data in channel['responseData'].items():
            # print(impulse_response)
            with open('%s_%s_%s.txt' % (in_file_wo_ext, measurement, speaker), 'w') as fp:
                fp.write(header)
                fp.write('\n')
                fp.write('\n'.join(data))
                fp.close()

if __name__ == "__main__":
    main()
