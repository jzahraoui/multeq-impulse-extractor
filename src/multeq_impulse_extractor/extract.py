#!/usr/bin/python3

import argparse
import pathlib
import dataclasses
from array import ArrayType
import json
import sys
import os

ady_in_file = sys.argv[1]
script_dir = os.path.dirname(__file__)
header_template_file = os.path.join(script_dir, 'header.template')
perfect_speaker_file = os.path.join(script_dir, 'perfect_speaker.json')


@dataclasses.dataclass
class Config:
    default: bool
    clean: bool
    filter: pathlib.Path
    extract: bool


class multeqTool:
    def __init__(self, config: Config):
        self.config: Config = config

    def process(self, in_file: pathlib.Path, out_file: pathlib.Path):
        if not in_file.is_file():
            raise RuntimeError(
                f'Input file {in_file.absolute()} is not a file')

        in_file_wo_ext = os.path.splitext(in_file.name)[0]

        if out_file == None:
            out_file = in_file_wo_ext + ".result.ady"

        with open(in_file, 'r') as jsonFile:
            in_json = json.load(jsonFile)  # Read the JSON into the buffer

        if self.config.extract:
            self.extract(in_file_wo_ext, in_json)
        if self.config.default:
            in_json = self.default(in_json)
        if self.config.clean:
            in_json = self.clean_response(in_json)
        if self.config.filter:
            if not self.config.filter.is_dir():
                raise RuntimeError(
                    f'Incorrect path to filter directory: {self.config.filter.absolute()}')
            in_json = self.inject_filters(in_json)

        # Save our changes to JSON file
        with open(out_file, "w+") as outjsonFile:
            json.dump(in_json, outjsonFile)
            outjsonFile.close()
            print("output file succefull: " + outjsonFile.name) 

    def extract(self, in_file_wo_ext: str, in_json):
        print("extracting response data...", end = "")

        with open(header_template_file, 'r') as header_file:
            header = header_file.read()
            header_file.close()

        channels = dict((item['commandId'], item)
                        for item in in_json['detectedChannels'])
        for speaker, channel in channels.items():
            for measurement, data in channel['responseData'].items():
                # print(impulse_response)
                with open('%s_%s_%s.txt' % (in_file_wo_ext, measurement, speaker), 'w') as fp:
                    fp.write(header)
                    fp.write('\n')
                    fp.write('\n'.join(data))
                    fp.close()
        
        print("done")

    def default(self, in_json):
        print("reseting default values...", end = "")

        detected_channel_count = len(in_json['detectedChannels'])

        for i in range(0, detected_channel_count):
            in_json['detectedChannels'][i]['customDistance'] = '3'
            in_json['detectedChannels'][i]['customLevel'] = '0'
            in_json['detectedChannels'][i]['customCrossover'] = 'F'
            in_json['detectedChannels'][i]['customSpeakerType'] = 'L'
            in_json['detectedChannels'][i]['midrangeCompensation'] = 'false'
        
        print("done")

        return in_json

    def clean_response(self, in_json):
        print("set perfect speaker response data...", end = "")

        with open(perfect_speaker_file, 'r') as perfect_speaker:
            perfect_speaker_data = json.load(perfect_speaker)

        detected_channel_count = len(in_json['detectedChannels'])

        for i in range(0, detected_channel_count):
            for measurement, data in in_json['detectedChannels'][i]['responseData'].items():
                in_json['detectedChannels'][i]['responseData'][measurement] = perfect_speaker_data
        
        print("done")

        return in_json

    def inject_filters(self, in_json):
        print("inject filters...")

        detected_channel_count = len(in_json['detectedChannels'])

        for i in range(0, detected_channel_count):
            speaker = in_json['detectedChannels'][i]['commandId']
            speaker_filter_file = self.config.filter.name + os.sep + speaker + '.txt'
            if not os.path.exists(speaker_filter_file):
                print("cannot access '%s': No such file or directory, skipping" % (
                    speaker_filter_file))
                continue
            with open(speaker_filter_file, 'r', encoding="ISO-8859-1") as fp:
                filter_data = []
                for line in fp:
                    if '\n' == line:
                        continue
                    if line.startswith('*'):
                        continue
                    line_values = line.rstrip().split(' ')
                    filter_data.append('{%s, %s}' %
                                       (line_values[0], line_values[1]))
                in_json['detectedChannels'][i]['customTargetCurvePoints'] = filter_data
        
        print("inject filters done")

        return in_json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-i', '--input',
        help='Path to ady file',
        type=pathlib.Path,
        required=True,
    )
    parser.add_argument(
        '-o', '--output',
        help='Path to output result file, if not specified will use .result.ady extention. WARNING: it will be overwrited',
        type=pathlib.Path
    )
    parser.add_argument(
        '-d', '--default',
        help='set default values : \n - 0db level\n - distance set to 3m\n - speaker type set to large\n - midrange compensation off',
        action='store_true',
    )
    parser.add_argument(
        '-c', '--clean',
        help='Output a file with cleaned response data',
        action='store_true',
    )
    parser.add_argument(
        '-f', '--filter',
        help='specify folder where resides your filters files. process will put them into custum target curve related chanels',
        type=pathlib.Path
    )
    parser.add_argument(
        '-e', '--extract',
        help='Decode one channel at a time',
        action='store_true',
    )
    args = parser.parse_args()
    args_dataclass = Config(
        default=args.default,
        clean=args.clean,
        filter=args.filter,
        extract=args.extract,
    )

    multeq = multeqTool(args_dataclass)
    multeq.process(args.input, args.output)


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        print(e)
