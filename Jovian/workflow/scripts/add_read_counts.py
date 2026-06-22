#!/usr/bin/env python3
"""
Insert read counts into a CSV by matching sample + scaffold IDs.

File 1: CSV
  column 1 = sample
  column 2 = scaffold ID

File 2: TSV
  column 1 = read count
  column 2 = scaffold ID
  column 3 = sample

Both files must have headers. Header names are ignored; matching uses column
positions only.
"""

import argparse
import csv
from collections import defaultdict


def normalize_scaffold(scaffold):
    return scaffold.split("_cov", 1)[0]


def read_counts_table(path):
    counts = defaultdict(int)

    with open(path, newline="") as handle:
        reader = csv.reader(handle, delimiter="\t")
        next(reader, None)

        for line_number, row in enumerate(reader, start=2):
            if not row or all(not value.strip() for value in row):
                continue
            if len(row) < 3:
                raise ValueError(
                    f"{path}: line {line_number} has fewer than 3 columns"
                )

            try:
                read_count = int(row[0])
            except ValueError as exc:
                raise ValueError(
                    f"{path}: line {line_number} has a non-integer read count: {row[0]!r}"
                ) from exc

            scaffold = normalize_scaffold(row[1])
            sample = row[2]
            counts[(sample, scaffold)] += read_count

    return counts


def add_counts_to_csv(input_csv, counts_tsv, output_csv, column_name, missing_value):
    counts = read_counts_table(counts_tsv)

    with open(input_csv, newline="") as in_handle, open(
        output_csv, "w", newline=""
    ) as out_handle:
        reader = csv.reader(in_handle)
        writer = csv.writer(out_handle)

        header = next(reader, None)
        if header is None:
            raise ValueError(f"{input_csv}: file is empty")
        if len(header) < 2:
            raise ValueError(f"{input_csv}: header has fewer than 2 columns")

        writer.writerow(header[:2] + [column_name] + header[2:])

        for line_number, row in enumerate(reader, start=2):
            if not row or all(not value.strip() for value in row):
                writer.writerow(row)
                continue
            if len(row) < 2:
                raise ValueError(
                    f"{input_csv}: line {line_number} has fewer than 2 columns"
                )

            sample = row[0]
            scaffold = normalize_scaffold(row[1])
            read_count = counts.get((sample, scaffold), missing_value)
            writer.writerow(row[:2] + [read_count] + row[2:])


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Insert read counts as column 3 in a CSV by matching sample + scaffold "
            "against a read-count TSV."
        )
    )
    parser.add_argument("input_csv", help="CSV file: column 1 sample, column 2 scaffold")
    parser.add_argument(
        "counts_tsv",
        help="TSV file: column 1 read count, column 2 scaffold, column 3 sample",
    )
    parser.add_argument("output_csv", help="Output CSV path")
    parser.add_argument(
        "--column-name",
        default="read_count",
        help="Name for the inserted column. Default: read_count",
    )
    parser.add_argument(
        "--missing-value",
        default="",
        help="Value to write when no matching count is found. Default: empty string",
    )

    args = parser.parse_args()
    add_counts_to_csv(
        args.input_csv,
        args.counts_tsv,
        args.output_csv,
        args.column_name,
        args.missing_value,
    )


if __name__ == "__main__":
    main()
