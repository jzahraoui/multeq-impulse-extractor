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

script_dir = os.path.dirname(__file__)
header_template_file = os.path.join(script_dir, 'header.template')
perfect_speaker_file = os.path.join(script_dir, 'perfect_speaker.json')
title = "multeq-impulse-extractor"


@dataclasses.dataclass
class Config:
    default: bool
    clean: bool
    filter: pathlib.Path
    extract: bool


class adyTool:
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
            in_json = orjson.loads(jsonFile.read())

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
            in_json = self.inject_filters(in_json, self.config.filter.name)

        # Save our changes to JSON file
        with open(out_file, "w+") as outjsonFile:
            json.dump(in_json, outjsonFile)
            outjsonFile.close()
            print("output file succefull: " + outjsonFile.name)

    def extract(self, dest_dir: str, in_json):
        print("extracting response data...", end="")

        with open(header_template_file, 'r') as header_file:
            header = header_file.read()
            header_file.close()

        channels = dict((item['commandId'], item)
                        for item in in_json['detectedChannels'])
        for speaker, channel in channels.items():
            for measurement, data in channel['responseData'].items():
                # print(impulse_response)
                with open('%s%s%s_%s.txt' % (dest_dir, os.sep, measurement, speaker), 'w') as fp:
                    fp.write(header)
                    fp.write('\n')
                    fp.write('\n'.join(data))
                    fp.close()

        print("done")

    def extract_freq(self, in_json, dest_dir: str):
        print("extracting response data to frequencie format...", end="")

        channels = dict((item['commandId'], item)
                        for item in in_json['detectedChannels'])
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

    def default(self, in_json):
        print("reseting default values...", end="")

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
        print("set perfect speaker response data...", end="")

        with open(perfect_speaker_file, 'rb') as perfect_speaker:
            perfect_speaker_data = orjson.loads(perfect_speaker.read())

        detected_channel_count = len(in_json['detectedChannels'])

        for i in range(0, detected_channel_count):
            for measurement, data in in_json['detectedChannels'][i]['responseData'].items():
                in_json['detectedChannels'][i]['responseData'][measurement] = perfect_speaker_data

        print("done")

        return in_json

    def inject_filters(self, in_json, filter_source_dir):
        print("inject filters...")

        detected_channel_count = len(in_json['detectedChannels'])

        for i in range(0, detected_channel_count):
            speaker = in_json['detectedChannels'][i]['commandId']
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
                    line_values = line.rstrip().replace('\t',' ').split(' ')
                    filter_data.append('{%s, %s}' %
                                       (line_values[0], line_values[1]))
                in_json['detectedChannels'][i]['customTargetCurvePoints'] = filter_data
                print(speaker + " imported successfully")

        print("inject filters done")

        return in_json

    def refresh_edit(self, in_json):
        # for Lines in in_json: # Around 3 millions iterations
        #     self.txt_edit.delete(f'{Lines}.0', f'{Lines}.end+1c')
        #     self.txt_edit.insert(f'{Lines}.0', Lines)
        self.txt_edit.config(state=tk.NORMAL)
        self.txt_edit.delete("1.0", tk.END)
        self.txt_edit.insert("1.0", json.dumps(in_json, indent=2))
        self.txt_edit.config(state=tk.DISABLED)

    def get_from_edit(self):
        text = self.txt_edit.get("1.0", tk.END)
        return orjson.loads(text)

    def extract_action(self):
        dest_dir = askdirectory(
            title="Destination folder", parent=self.window, mustexist=True)

        if not dest_dir:
            return

        in_json = self.get_from_edit()
        self.extract(dest_dir, in_json)

    def extract_freq_action(self):
        dest_dir = askdirectory(
            title="Destination folder", parent=self.window, mustexist=True)

        if not dest_dir:
            return

        in_json = self.get_from_edit()
        self.extract_freq(in_json=in_json, dest_dir=dest_dir)

    def default_action(self):
        in_json = self.get_from_edit()
        out_json = self.default(in_json)
        self.refresh_edit(out_json)

    def clean_response_action(self):
        in_json = self.get_from_edit()
        out_json = self.clean_response(in_json)
        self.refresh_edit(out_json)

    def inject_filters_action(self):
        filter_source_dir = askdirectory(parent=self.window,
                                         title="Source folder", mustexist=True)

        if not filter_source_dir:
            return

        in_json = self.get_from_edit()
        out_json = self.inject_filters(
            in_json=in_json, filter_source_dir=filter_source_dir)
        self.refresh_edit(out_json)

    def load_file(self):
        in_file = askopenfilename(title="Open Your musurement file", parent=self.window,
                                  filetypes=[
                                      ('ady Files', '*.ady'), ('All Files', '*.*')])

        if not in_file:
            return

        in_json = {}
        try:
            with open(in_file, 'rb') as jsonFile:
                # Read the JSON into the buffer
                in_json = orjson.loads(jsonFile.read())
                jsonFile.close()
        except FileNotFoundError():
            print(e)

        self.refresh_edit(in_json)
        self.set_title(f"{title} - {in_file}")

    def save_file(self):
        """Save the current file as a new file."""
        filepath = asksaveasfilename(parent=self.window,
                                     defaultextension=".ady",
                                     filetypes=[("ady Files", "*.ady"),
                                                ("All Files", "*.*")],
                                     )
        if not filepath:
            return

        in_json = self.get_from_edit()
        with open(filepath, mode="w", encoding="utf-8") as output_file:
            json.dump(in_json, output_file)

        self.set_title(f"{title} - {filepath}")

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

        self.set_title(title)

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

        btn_clean = tk.Button(frm_buttons, text="clean",
                              command=self.clean_response_action)
        btn_default = tk.Button(frm_buttons, text="default",
                                command=self.default_action)
        btn_extract = tk.Button(frm_buttons, text="extract",
                                command=self.extract_action)
        btn_inject_filters = tk.Button(
            frm_buttons, text="inject filters", command=self.inject_filters_action)
        btn_create_filters = tk.Button(frm_buttons, text="create filters")
        btn_extract_freq = tk.Button(
            frm_buttons, text="extract freq", command=self.extract_freq_action)

        btn_open.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        btn_save.grid(row=1, column=0, sticky="ew", padx=5)

        btn_clean.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        btn_default.grid(row=3, column=0, sticky="ew", padx=5)
        btn_extract.grid(row=4, column=0, sticky="ew", padx=5, pady=5)
        btn_inject_filters.grid(row=5, column=0, sticky="ew", padx=5)
        # btn_create_filters.grid(row=6, column=0, sticky="ew", padx=5, pady=5)
        btn_extract_freq.grid(row=7, column=0, sticky="ew", padx=5, pady=5)

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
