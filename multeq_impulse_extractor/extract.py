#!/usr/bin/python3

from array import ArrayType
import json
import sys
import os

ady_in_file = sys.argv[1]
script_dir = os.path.dirname(__file__)
header_template_file = os.path.join(script_dir, 'header.template')
perfect_speaker_file = os.path.join(script_dir, 'perfect_speaker.json')
filter_folder = 'filter/'


def main():
    extract(ady_in_file)
    cleaned_file = clean_response(ady_in_file)
    print('cleaned file: ' + cleaned_file)
    corrected_file = inject_filters(ady_in_file)
    print('corrected file: ' + corrected_file)


def extract(in_file):

    in_file_wo_ext = os.path.splitext(in_file)[0]

    with open(in_file, 'r') as jsonFile:
        in_json = json.load(jsonFile)  # Read the JSON into the buffer

    with open(header_template_file, 'r') as header_file:
        header = header_file.read()
        header_file.close()

    channels = dict((item['commandId'], item) for item in in_json['detectedChannels'])
    for speaker, channel in channels.items():
        for measurement, data in channel['responseData'].items():
            # print(impulse_response)
            with open('%s_%s_%s.txt' % (in_file_wo_ext, measurement, speaker), 'w') as fp:
                fp.write(header)
                fp.write('\n')
                fp.write('\n'.join(data))
                fp.close()


def clean_response(in_file):

    in_file_wo_ext = os.path.splitext(in_file)[0]

    with open(in_file, 'r') as jsonFile:
        in_json = json.load(jsonFile)  # Read the JSON into the buffer

    with open(perfect_speaker_file, 'r') as perfect_speaker:
        perfect_speaker_data = json.load(perfect_speaker)

    detected_channel_count = len(in_json['detectedChannels'])

    for i in range(0, detected_channel_count):
        in_json['detectedChannels'][i]['customDistance'] = '3'
        in_json['detectedChannels'][i]['customLevel'] = '0'
        in_json['detectedChannels'][i]['customCrossover'] = 'F'
        in_json['detectedChannels'][i]['customSpeakerType'] = 'L'
        for measurement, data in in_json['detectedChannels'][i]['responseData'].items():
            in_json['detectedChannels'][i]['responseData'][measurement] = perfect_speaker_data

    out_file = in_file_wo_ext + ".cleaned.ady"

    # Save our changes to JSON file
    with open(out_file, "w+") as outjsonFile:
        json.dump(in_json, outjsonFile)

    return out_file


def inject_filters(in_file):

    in_file_wo_ext = os.path.splitext(in_file)[0]

    with open(in_file, 'r') as jsonFile:
        in_json = json.load(jsonFile)  # Read the JSON into the buffer

    with open(perfect_speaker_file, 'r') as perfect_speaker:
        perfect_speaker_data = json.load(perfect_speaker)

    detected_channel_count = len(in_json['detectedChannels'])

    for i in range(0, detected_channel_count):
        for measurement, data in in_json['detectedChannels'][i]['responseData'].items():
            in_json['detectedChannels'][i]['responseData'][measurement] = perfect_speaker_data
        speaker = in_json['detectedChannels'][i]['commandId']
        speaker_filter_file = filter_folder + speaker + '.txt'
        if not os.path.exists(speaker_filter_file):
            continue
        with open(speaker_filter_file, 'r', encoding="ISO-8859-1") as fp:
            filter_data = []
            for line in fp:
                if '\n' == line:
                    continue
                if line.startswith('*'):
                    continue
                line_values = line.rstrip().split(' ')
                filter_data.append('{%s, %s}' % (line_values[0], line_values[1]))
            in_json['detectedChannels'][i]['customTargetCurvePoints'] = filter_data

    out_file = in_file_wo_ext + ".corrected.ady"

    # Save our changes to JSON file
    with open(out_file, "w+") as outjsonFile:
        json.dump(in_json, outjsonFile)

    return out_file


if __name__ == "__main__":
    main()
