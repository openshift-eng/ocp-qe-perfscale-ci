#!/usr/bin/env python3

import argparse
import logging
from es_search import ESSearch
from sheets import Sheets
from typing import Dict
import csv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(module)s:%(lineno)d %(levelname)s %(message)s",
)
logger = logging.getLogger("perfsheets")

# cell range for netobserv perf sheet comparison
SHEET_CELL_RANGE = "A1:G1000"
NETOBSERV_ES_INDEX = "prod-netobserv-operator-metadata"
EMAIL_TO_SHARE = "openshift-netobserv-team@redhat.com"


def get_values_from_es(uuid) -> tuple:
    """
    Gets release and NOPE_JIRA field from netobserv metadata ES index
    """
    es = ESSearch(NETOBSERV_ES_INDEX)
    uuidMatchRes = es.match({"uuid.keyword": uuid})

    (noo_bundle_version, jira) = ("", "")
    if uuidMatchRes:
        try:
            if (
                uuidMatchRes["noo_bundle_version"]
                and uuidMatchRes["noo_bundle_version"] != "N/A"
            ):
                noo_bundle_version = uuidMatchRes["noo_bundle_version"]
        except KeyError:
            logger.info("NOO bundle version not found")

        noo_bundle_version += "/" + uuidMatchRes.get("iso_timestamp", 0)

        try:
            if uuidMatchRes["jira"] != "N/A":
                jira = uuidMatchRes["jira"]
        except KeyError:
            logger.info("JIRA field not found in ES index")
    return (noo_bundle_version, jira)


def create_uuid_replace_map(*uuids) -> Dict[str, tuple]:
    """
    Create a map to associate UUID to their
    NOO Bundle version and JIRA metadata
    """
    noo_versions = {}
    for u in uuids:
        if u:
            (noo_version, jira) = get_values_from_es(u)
        replace_str = ""
        if noo_version:
            replace_str += noo_version
        if jira:
            if replace_str:
                replace_str += "/" + jira
            else:
                replace_str += jira
        if replace_str:
            noo_versions[u] = replace_str
        else:
            # if none of the metadata found; keep UUID as is
            noo_versions[u] = u
    return noo_versions


def write_comparison(csvfile):
    sheet_values = []
    with open(csvfile, "r") as comp_file:
        csvreader = csv.reader(comp_file)
        header = next(csvreader)
        uuids = [header[-2], header[-1]]
        uuid_replace = create_uuid_replace_map(*uuids)
        new_header = []
        for val in header:
            if val in uuids and uuid_replace[val]:
                new_header.append(uuid_replace[val])
            else:
                new_header.append(val)
        sheet_values.append(new_header)
        for row in csvreader:
            if "metric_name" not in row:
                sheet_values.append(row)
    return sheet_values


def write_metrics(csvfile):
    with open(csvfile, "r") as comp_file:
        csvreader = csv.reader(comp_file)
        return list(csvreader)


def argparser():
    """
    Parse arguments
    """
    parser = argparse.ArgumentParser(
        prog="Tool to update NOO Perf tests comparison sheets"
    )

    parser.add_argument(
        "--service-account",
        help="Google service account file",
        required=True,
    )
    parser.add_argument(
        "--csv-file",
        help="Metrics CSV file to generate gsheet",
        required=True,
    )
    parser.add_argument(
        "--name",
        help="Spreadsheet name",
        required=True,
    )
    parser.add_argument(
        "--comparison",
        action="store_true",
        help="Define if csv file is a comparison file or metrics sheet",
    )

    return parser.parse_args()


def main():
    args = argparser()
    gsheets = Sheets(None, SHEET_CELL_RANGE, args.service_account)
    gsheets.create(args.name)
    if args.comparison:
        sheet_data = write_comparison(
            args.csv_file,
        )
    else:
        sheet_data = write_metrics(
            args.csv_file,
        )
    gsheets.update_values(sheet_data)
    gsheets.create_permission(EMAIL_TO_SHARE)
    gsheets.auto_resize_columns()
    logger.info(
        f"Successfully wrote to google sheet: https://docs.google.com/spreadsheets/d/{gsheets.sheetid}"
    )


if __name__ == "__main__":
    main()
