
from array import ArrayType
import json
import sys
import os

header_file = open('header.template', 'r')
header = header_file.read()
header_file.close()

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
