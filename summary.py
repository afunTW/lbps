import os
import glob
import json
import csv


def main():
    trace_dir = glob.glob('metadata/*')

    for repo in trace_dir:
        if repo.split(os.sep)[-1] not in ['equal_load', 'hot_spot']: continue
        summary = open(repo + '/' + repo.split(os.sep)[-1] + '.csv', 'w+')
        csv_writer = csv.writer(summary)
        trace_file = glob.glob(repo + '/*.json')
        trace_file = sorted(trace_file)
        metadata = {}

        for filename in trace_file:
            with open(filename, 'r') as f:
                metadata = json.load(f)
                algorithm = filename.split(os.sep)[-1]
                metadata = sorted(metadata , key = lambda x: x['lambda'])
                for count, meta in enumerate(metadata):
                    header = [
                        'lambda', 'rn-pse', 'ue-pse', 'ue-delay',
                        'pse-fairness', 'delay-fairness', 'rn-collision'
                    ]
                    data = [meta[i] for i in header if i in meta.keys()]
                    header = ['algorithm'] + header
                    data = [algorithm] + data

                    if count == 0: csv_writer.writerow(header)
                    csv_writer.writerow(data)

        summary.close()

if __name__ == '__main__':
    main()