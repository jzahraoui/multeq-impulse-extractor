#!/usr/bin/python3

import argparse
import pathlib
import dataclasses
from array import ArrayType
import json
import os
import numpy as np
import tkinter as tk
from tkinter.filedialog import askdirectory, askopenfilename, asksaveasfilename
import orjson
import re

script_dir = os.path.dirname(__file__)


@dataclasses.dataclass
class Config:
    default: bool
    clean: bool
    filter: pathlib.Path
    extract: bool


class adyTool:

    header_template_file = 'header.template'
    application_title = 'multeq-impulse-extractor'
    header = ''
    in_json = {}

    def __init__(self, config: Config):
        self.config: Config = config

    def process(self, in_file: pathlib.Path, out_file: pathlib.Path):
        if not in_file.is_file():
            raise RuntimeError(
                f'Input file {in_file.absolute()} is not a file')

        in_file_wo_ext = os.path.splitext(in_file.name)[0]

        if out_file == None:
            out_file = in_file_wo_ext + ".result.ady"

        with open(in_file, 'rb') as jsonFile:
            # Read the JSON into the buffer
            self.in_json = orjson.loads(jsonFile.read())

        if self.config.extract:
            self.extract(in_file_wo_ext)
        if self.config.default:
            self.default()
        if self.config.clean:
            self.clean_response()
        if self.config.filter:
            if not self.config.filter.is_dir():
                raise RuntimeError(
                    f'Incorrect path to filter directory: {self.config.filter.absolute()}')
            self.inject_target_curve(self.config.filter.name)

        # Save our changes to JSON file
        with open(out_file, "w+") as outjsonFile:
            json.dump(self.in_json, outjsonFile)
            outjsonFile.close()
            print("output file succefull: " + outjsonFile.name)

    def extract(self, dest_dir: str):
        print("extracting response data...", end="")

        channels = dict((item['commandId'], item)
                        for item in self.in_json['detectedChannels'])
        for speaker, channel in channels.items():
            for measurement, data in channel['responseData'].items():
                # print(impulse_response)
                with open('%s%s%s_%s.txt' % (dest_dir, os.sep, measurement, speaker), 'w') as fp:
                    fp.write(self.getHeaderContent())
                    fp.write('\n')
                    fp.write('\n'.join(data))
                    fp.close()

        print("done")

    def extract_curve_filter(self, dest_dir: str, key: str):
        print("extracting curve filter data...", end="")

        if ('referenceCurveFilter' != key) and ('flatCurveFilter' != key):
            print("key " + key + "not valid")
            return

        channels = dict((item['commandId'], item)
                        for item in self.in_json['detectedChannels'])
        for speaker, channel in channels.items():
            for measurement, data in channel[key].items():
                str_data = [str(val) for val in data]
                # print(impulse_response)
                with open('%s%s%s_%s.txt' % (dest_dir, os.sep, measurement, speaker), 'w') as fp:
                    fp.write(self.getHeaderContent())
                    fp.write('\n')
                    fp.write('\n'.join(str_data))
                    fp.close()

        print("done")

    def getHeaderContent(self):
        if self.header == '':
            header_path_file = os.path.join(
                script_dir, self.header_template_file)
            with open(header_path_file, 'r') as header_file:
                self.header = header_file.read()
                header_file.close()
        return self.header

    def extract_freq(self, dest_dir: str):
        print("extracting response data to frequencie format...", end="")

        channels = dict((item['commandId'], item)
                        for item in self.in_json['detectedChannels'])
        for speaker, channel in channels.items():
            for measurement, data in channel['responseData'].items():
                data_nbr = [float(val) for val in data]
                sample_rate = 48000
                n = len(data)
                step = sample_rate/n
                mag = np.fft.rfft(data_nbr)
                freq = np.fft.rfftfreq(n, 1 / sample_rate)
                spl = 20 * np.log10(np.abs(mag)) + 75
                phase = np.angle(mag, deg=True)
                rew_fmt = '%10.6f', '%f', '%10.4f'
                filename = '%s%sfreq_%s_%s.txt' % (
                    dest_dir, os.sep, measurement, speaker)
                np.savetxt(filename, np.c_[
                    freq, spl, phase], fmt=rew_fmt, comments='*', header='Frequency Step: %s Hz' % step)
        print("done")

    def default(self):
        print("reseting default values...", end="")

        detected_channel_count = len(self.in_json['detectedChannels'])

        for i in range(0, detected_channel_count):
            self.in_json['detectedChannels'][i]['customDistance'] = '3'
            self.in_json['detectedChannels'][i]['customLevel'] = '0'
            self.in_json['detectedChannels'][i]['customCrossover'] = 'F'
            self.in_json['detectedChannels'][i]['customSpeakerType'] = 'L'
            self.in_json['detectedChannels'][i]['midrangeCompensation'] = 'false'

        print("done")

    def create_perfect_response(self):
        perfect_speaker_data = []
        perfect_speaker_data.append('1')
        for i in range(0, 16383):
            perfect_speaker_data.append('0')
        return perfect_speaker_data

    def clean_response(self):
        print("set perfect speaker response data...", end="")

        perfect_speaker_data = self.create_perfect_response()
        detected_channel_count = len(self.in_json['detectedChannels'])

        for i in range(0, detected_channel_count):
            for measurement in self.in_json['detectedChannels'][i]['responseData'].keys():
                self.in_json['detectedChannels'][i]['responseData'][measurement] = perfect_speaker_data

        print("done")

    def inject_target_curve(self, filter_source_dir):
        print("inject filters...")

        detected_channel_count = len(self.in_json['detectedChannels'])

        for i in range(0, detected_channel_count):
            speaker = self.in_json['detectedChannels'][i]['commandId']
            speaker_filter_file = filter_source_dir + os.sep + speaker + '.txt'
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
                    line_values = line.replace('\t', ' ').rstrip().split(' ')
                    filter_data.append('{%s, %s}' %
                                       (line_values[0], line_values[1]))
                self.in_json['detectedChannels'][i]['customTargetCurvePoints'] = filter_data
                print(speaker + " imported successfully")

        print("inject filters done")

    def inject_response(self, response_source_dir):
        print("inject response data...")

        detected_channel_count = len(self.in_json['detectedChannels'])

        for i in range(0, detected_channel_count):
            speaker = self.in_json['detectedChannels'][i]['commandId']

            regex = re.compile(r"^\d_" + re.escape(speaker) + r".txt")

            responses_files = [f.name for f in os.scandir(
                response_source_dir) if (f.is_file() and regex.match(f.name) is not None)]
            for filename in list(responses_files):
                position_index = filename[0]
                with open(response_source_dir + os.sep + filename, 'r', encoding="ISO-8859-1") as fp:
                    filter_data = []
                    for line in fp:
                        if '\n' == line:
                            continue
                        if line.startswith('*'):
                            continue
                        if "//" in line:
                            continue
                        line_value = line.replace('\t', ' ').rstrip()
                        filter_data.append(line_value)
                    self.in_json['detectedChannels'][i]['responseData'][position_index] = filter_data
                    print(filename + " imported successfully")

        print("inject response done")

    def inject_curve_filters(self, response_source_dir, key: str):
        print("inject curve filters data...")

        if ('referenceCurveFilter' != key) and ('flatCurveFilter' != key):
            print("key " + key + "not valid")
            return

        detected_channel_count = len(self.in_json['detectedChannels'])

        for i in range(0, detected_channel_count):
            speaker = self.in_json['detectedChannels'][i]['commandId']

            regex = re.compile(r"^\w{9,}_" + re.escape(speaker) + r".txt")

            responses_files = [f.name for f in os.scandir(
                response_source_dir) if (f.is_file() and regex.match(f.name) is not None)]
            for filename in list(responses_files):
                position_index = filename.split('_')[0]
                with open(response_source_dir + os.sep + filename, 'r', encoding="ISO-8859-1") as fp:
                    filter_data = []
                    for line in fp:
                        if '\n' == line:
                            continue
                        if line.startswith('*'):
                            continue
                        if "//" in line:
                            continue
                        line_value = line.replace('\t', ' ').rstrip()
                        filter_data.append(line_value)
                    self.in_json['detectedChannels'][i][key][position_index] = filter_data
                    print(filename + " imported successfully")

        print("inject response done")

    def refresh_edit(self):
        # for Lines in in_json: # Around 3 millions iterations
        #     self.txt_edit.delete(f'{Lines}.0', f'{Lines}.end+1c')
        #     self.txt_edit.insert(f'{Lines}.0', Lines)
        self.txt_edit.config(state=tk.NORMAL)
        self.txt_edit.delete("1.0", tk.END)
        self.txt_edit.insert("1.0", json.dumps(self.in_json, indent=2))
        self.txt_edit.config(state=tk.DISABLED)

    def get_from_edit(self):
        text = self.txt_edit.get("1.0", tk.END)
        return orjson.loads(text)

    def extract_action(self):
        dest_dir = askdirectory(
            title="Destination folder", parent=self.window, mustexist=True)

        if not dest_dir:
            return

        self.extract(dest_dir)

    def extract_curve_filter_action(self):
        dest_dir = askdirectory(
            title="Destination folder", parent=self.window, mustexist=True)

        if not dest_dir:
            return

        self.extract_curve_filter(dest_dir, "referenceCurveFilter")

    def extract_freq_action(self):
        dest_dir = askdirectory(
            title="Destination folder", parent=self.window, mustexist=True)

        if not dest_dir:
            return

        self.extract_freq(dest_dir=dest_dir)

    def default_action(self):
        self.default()
        self.refresh_edit()

    def clean_response_action(self):
        self.clean_response()
        self.refresh_edit()

    def inject_target_curve_action(self):
        filter_source_dir = askdirectory(parent=self.window,
                                         title="Source folder", mustexist=True)

        if not filter_source_dir:
            return

        self.inject_target_curve(filter_source_dir)
        self.refresh_edit()

    def inject_response_action(self):
        response_source_dir = askdirectory(parent=self.window,
                                           title="Source folder", mustexist=True)

        if not response_source_dir:
            return

        self.inject_response(response_source_dir)
        self.refresh_edit()

    def inject_curve_filter_action(self):
        response_source_dir = askdirectory(parent=self.window,
                                           title="Source folder", mustexist=True)

        if not response_source_dir:
            return

        self.inject_curve_filters(response_source_dir, "referenceCurveFilter")
        self.refresh_edit()

    def load_file(self):
        in_file = askopenfilename(title="Open Your musurement file", parent=self.window,
                                  filetypes=[
                                      ('ady Files', '*.ady'), ('All Files', '*.*')])

        if not in_file:
            return

        self.in_json = {}
        try:
            with open(in_file, 'rb') as jsonFile:
                # Read the JSON into the buffer
                self.in_json = orjson.loads(jsonFile.read())
                jsonFile.close()
        except FileNotFoundError():
            print(e)

        self.refresh_edit()
        self.set_title(f"{self.application_title} - {in_file}")

    def save_file(self):
        """Save the current file as a new file."""
        filepath = asksaveasfilename(parent=self.window,
                                     defaultextension=".ady",
                                     filetypes=[("ady Files", "*.ady"),
                                                ("All Files", "*.*")],
                                     )
        if not filepath:
            return

        with open(filepath, mode="w", encoding="utf-8") as output_file:
            json.dump(self.in_json, output_file)

        self.set_title(f"{self.application_title} - {filepath}")

    def toggle_detail_view(self):
        """
        This function toggles between expanding the tree and closing it.
        """
        if self.show_detail.get():
            childrens = self.tree.get_children()
            for child in childrens:
                self.expand_item(child)
        else:
            childrens = self.tree.get_children()
            for child in childrens:
                self.close_item(child)

    def set_title(self, title):
        """
        :param title: Its a <str> object.
        """
        self.window.title(title)

    def init_gui(self):

        self.window = tk.Tk()

        self.set_title(self.application_title)

        self.window.rowconfigure(0, minsize=800, weight=1)
        self.window.columnconfigure(1, minsize=800, weight=1)

        xscrollbar = tk.Scrollbar(self.window, orient=tk.HORIZONTAL)
        xscrollbar.grid(row=1, column=1, sticky="ew")

        yscrollbar = tk.Scrollbar(self.window)
        yscrollbar.grid(row=0, column=2, sticky="ns")

        self.txt_edit = tk.Text(self.window, bd=0,
                                xscrollcommand=xscrollbar.set,
                                yscrollcommand=yscrollbar.set, wrap=tk.NONE, state=tk.DISABLED)

        xscrollbar.config(command=self.txt_edit.xview)
        yscrollbar.config(command=self.txt_edit.yview)

        frm_buttons = tk.Frame(self.window, relief=tk.RAISED, bd=2)
        btn_open = tk.Button(frm_buttons, text="Open", command=self.load_file)
        btn_save = tk.Button(frm_buttons, text="Save As...",
                             command=self.save_file)

        btn_clean = tk.Button(frm_buttons, text="set perfect responses",
                              command=self.clean_response_action)
        btn_default = tk.Button(frm_buttons, text="set defaults settings",
                                command=self.default_action)
        btn_extract = tk.Button(frm_buttons, text="export IRs",
                                command=self.extract_action)
        btn_inject_target_curve = tk.Button(
            frm_buttons, text="import target curves", command=self.inject_target_curve_action)
        btn_inject_response = tk.Button(
            frm_buttons, text="import responses", command=self.inject_response_action)
        btn_extract_freq = tk.Button(
            frm_buttons, text="export responses", command=self.extract_freq_action)
        btn_extract_cf = tk.Button(
            frm_buttons, text="export curve filters", command=self.extract_curve_filter_action)
        btn_inject_cf = tk.Button(
            frm_buttons, text="import curve filters", command=self.inject_curve_filter_action)

        btn_open.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        btn_save.grid(row=1, column=0, sticky="ew", padx=5)

        btn_default.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        btn_inject_target_curve.grid(row=3, column=0, sticky="ew", padx=5)
        btn_clean.grid(row=4, column=0, sticky="ew", padx=5, pady=5)
        btn_inject_response.grid(row=5, column=0, sticky="ew", padx=5)
        btn_extract.grid(row=6, column=0, sticky="ew", padx=5, pady=5)
        btn_extract_freq.grid(row=7, column=0, sticky="ew", padx=5)
        btn_extract_cf.grid(row=8, column=0, sticky="ew", padx=5, pady=5)
        btn_inject_cf.grid(row=9, column=0, sticky="ew", padx=5)

        frm_buttons.grid(row=0, column=0, sticky="ns")
        self.txt_edit.grid(row=0, column=1, sticky="nsew")

        show_detail = tk.IntVar()
        check_expand_all = tk.Checkbutton(self.window, text="Expand All", variable=show_detail, onvalue=1, offvalue=0,
                                          command=self.toggle_detail_view)
        # check_expand_all.grid(row=0, column=3, sticky="ns")

        self.window.mainloop()


def main():

    args_dataclass = Config(
        default=False,
        clean=False,
        filter="",
        extract=False,
    )
    multeq = adyTool(args_dataclass)
    multeq.init_gui()


def main_console():
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

    multeq = adyTool(args_dataclass)
    multeq.process(args.input, args.output)


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        print(e)
