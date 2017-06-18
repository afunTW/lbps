import os
import glob
import json
import csv


def main():
    trace_dir = glob.glob('metadata/*')

    for repo in trace_dir:
        summary = open(repo + '/outfile.csv', 'w+')
        csv_writer = csv.writer(summary)
        trace_file = glob.glob(repo + '/*.json')
        metadata = {}

        for filename in trace_file:
            with open(filename, 'r') as f:
                metadata[filename] = json.load(f)

        for k, v in metadata.items():
            algorithm = k.split(os.sep)[-1]
            v = sorted(v , key = lambda x: x['lambda'])
            for count, meta in enumerate(v):
                header = [
                    'lambda', 'rn-pse', 'ue-pse', 'ue-delay',
                    'pse-fairness', 'delay-fairness', 'rn-collision'
                ]
                data = [meta[i] for i in header]
                header = ['algorithm'] + header
                data = [algorithm] + data

                if count == 0: csv_writer.writerow(header)
                csv_writer.writerow(data)
        summary.close()

if __name__ == '__main__':
    main()