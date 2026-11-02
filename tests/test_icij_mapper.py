"""End-to-end tests: run icij_mapper.py on a small set of ICIJ-format csv files and check its output.

Needs the Senzing mapper-base project (the mapper imports base_mapper): set MAPPER_BASE_PATH to its src
directory, e.g. MAPPER_BASE_PATH=../mapper-base/src pytest tests
"""

import csv
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

MAPPER = Path(__file__).resolve().parent.parent / "src" / "icij_mapper.py"

HEADERS = {
    "nodes-entities.csv": "node_id,name,original_name,former_name,jurisdiction,jurisdiction_description,company_type,"
    "address,internal_id,incorporation_date,inactivation_date,struck_off_date,dorm_date,status,service_provider,"
    "ibcRUC,country_codes,countries,sourceID,valid_until,note",
    "nodes-intermediaries.csv": "node_id,name,status,internal_id,address,countries,country_codes,sourceID,valid_until,note",
    "nodes-officers.csv": "node_id,name,countries,country_codes,sourceID,valid_until,note",
    "nodes-addresses.csv": "node_id,address,name,countries,country_codes,sourceID,valid_until,note",
    "nodes-others.csv": "node_id,name,type,incorporation_date,struck_off_date,closed_date,jurisdiction,"
    "jurisdiction_description,countries,country_codes,sourceID,valid_until,note",
    "relationships.csv": "node_id_start,node_id_end,rel_type,link,status,start_date,end_date,sourceID",
}

ROWS = {
    "nodes-entities.csv": [
        {
            "node_id": "100",
            "name": "ACME HOLDINGS LIMITED",
            "jurisdiction": "BVI",
            "company_type": "Business Company",
            "incorporation_date": "01-JAN-2001",
            "status": "Active",
            "country_codes": "GBR;VGB",
            "sourceID": "Panama Papers",
            "note": "a note",
        },
    ],
    # 200 is both an intermediary and an officer: the same real entity in two node files
    "nodes-intermediaries.csv": [
        {
            "node_id": "200",
            "name": "Jane Example",
            "status": "ACTIVE",
            "country_codes": "GBR",
            "sourceID": "Offshore Leaks",
        },
    ],
    "nodes-officers.csv": [
        {"node_id": "200", "name": "Jane Example", "country_codes": "GBR", "sourceID": "Offshore Leaks"},
        {"node_id": "300", "name": "John Example", "country_codes": "GBR", "sourceID": "Offshore Leaks"},
    ],
    "nodes-addresses.csv": [
        {"node_id": "900", "address": "1 High Street London", "country_codes": "GBR", "sourceID": "Offshore Leaks"},
    ],
    "nodes-others.csv": [],
    "relationships.csv": [
        {
            "node_id_start": "200",
            "node_id_end": "100",
            "rel_type": "officer_of",
            "link": "director of",
            "start_date": "2004-12-18",
            "sourceID": "Offshore Leaks",
        },
        {
            "node_id_start": "200",
            "node_id_end": "900",
            "rel_type": "registered_address",
            "link": "registered address",
            "sourceID": "Offshore Leaks",
        },
        {
            "node_id_start": "300",
            "node_id_end": "100",
            "rel_type": "officer_of",
            "link": "shareholder of",
            "start_date": "2001-01-01",
            "end_date": "2005-01-01",
            "sourceID": "Offshore Leaks",
        },
        {
            "node_id_start": "100",
            "node_id_end": "900",
            "rel_type": "registered_address",
            "link": "registered address",
            "sourceID": "Panama Papers",
        },
    ],
}

# Senzing feature attributes the mapper writes; none of them may appear at the root.
FEATURE_ATTRIBUTES = {
    "RECORD_TYPE",
    "NAME_TYPE",
    "NAME_ORG",
    "NAME_FULL",
    "ADDR_TYPE",
    "ADDR_FULL",
    "COUNTRY_OF_ASSOCIATION",
    "GROUP_ASSOCIATION_ORG_NAME",
    "REL_ANCHOR_DOMAIN",
    "REL_ANCHOR_KEY",
    "REL_POINTER_DOMAIN",
    "REL_POINTER_KEY",
    "REL_POINTER_ROLE",
    "REL_POINTER_FROM_DATE",
    "REL_POINTER_THRU_DATE",
}


def write_inputs(folder: Path) -> None:
    for name, header in HEADERS.items():
        fields = header.split(",")
        with open(folder / name, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for row in ROWS[name]:
                writer.writerow(row)


@pytest.fixture(name="mapped", scope="module")
def fixture_mapped(tmp_path_factory):
    base = os.environ.get("MAPPER_BASE_PATH")
    assert base, "set MAPPER_BASE_PATH to the mapper-base src directory"
    inputs = tmp_path_factory.mktemp("input")
    write_inputs(inputs)
    os.chmod(inputs, 0o555)  # the mapper must not write into the input folder
    out_dir = tmp_path_factory.mktemp("output")
    output = out_dir / "icij.jsonl"
    env = dict(os.environ, PYTHONPATH=base)
    result = subprocess.run(
        [sys.executable, str(MAPPER), "-i", str(inputs), "-o", str(output)],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    os.chmod(inputs, 0o755)
    assert result.returncode == 0, result.stdout + result.stderr
    assert sorted(p.name for p in out_dir.iterdir()) == ["icij.jsonl"], "work database left behind"
    return {r["RECORD_ID"]: r for r in map(json.loads, output.read_text(encoding="utf-8").splitlines())}


def features(record, key):
    return [f for f in record["FEATURES"] if key in f]


def test_every_record_is_features_shaped(mapped):
    for record in mapped.values():
        assert set(record) & FEATURE_ATTRIBUTES == set(), record["RECORD_ID"]
        lists = [k for k, v in record.items() if isinstance(v, (list, dict)) and k != "FEATURES"]
        assert not lists, lists
        for feature in record["FEATURES"]:
            assert feature and all(v not in (None, "") for v in feature.values()), feature


def test_organization_payload_and_features(mapped):
    org = mapped["100"]
    assert org["DATA_SOURCE"] == "ICIJ"
    assert (org["ICIJ_SOURCE"], org["NODE_TYPE"], org["Jurisdiction"], org["Status"]) == (
        "Panama Papers",
        "ENTITY",
        "BVI",
        "Active",
    )
    assert (org["COMPANY_TYPE"], org["INCORPORATED"], org["NOTES"]) == ("Business Company", "01-JAN-2001", "a note")
    assert features(org, "RECORD_TYPE") == [{"RECORD_TYPE": "ORGANIZATION"}]
    assert features(org, "NAME_ORG") == [{"NAME_TYPE": "PRIMARY", "NAME_ORG": "ACME HOLDINGS LIMITED"}]
    assert [f["COUNTRY_OF_ASSOCIATION"] for f in features(org, "COUNTRY_OF_ASSOCIATION")] == ["BVI", "GBR", "VGB"]
    assert features(org, "ADDR_FULL") == [{"ADDR_TYPE": "BUSINESS", "ADDR_FULL": "1 High Street London"}]
    assert features(org, "REL_ANCHOR_KEY") == [{"REL_ANCHOR_DOMAIN": "ICIJ_ID", "REL_ANCHOR_KEY": "100"}]


def test_pointer_keys_are_strings_with_role_and_dates(mapped):
    pointers = features(mapped["300"], "REL_POINTER_KEY")
    assert pointers == [
        {
            "REL_POINTER_DOMAIN": "ICIJ_ID",
            "REL_POINTER_KEY": "100",
            "REL_POINTER_ROLE": "shareholder of",
            "REL_POINTER_FROM_DATE": "2001-01-01",
            "REL_POINTER_THRU_DATE": "2005-01-01",
        }
    ]
    anchors = {f["REL_ANCHOR_KEY"] for r in mapped.values() for f in features(r, "REL_ANCHOR_KEY")}
    for record in mapped.values():
        for pointer in features(record, "REL_POINTER_KEY"):
            assert isinstance(pointer["REL_POINTER_KEY"], str)
            assert pointer["REL_POINTER_KEY"] in anchors, pointer


def test_person_gets_group_association(mapped):
    person = mapped["300"]
    assert features(person, "NAME_FULL") == [{"NAME_TYPE": "PRIMARY", "NAME_FULL": "John Example"}]
    assert features(person, "GROUP_ASSOCIATION_ORG_NAME") == [{"GROUP_ASSOCIATION_ORG_NAME": "ACME HOLDINGS LIMITED"}]


def test_duplicate_node_ids_share_the_anchor_pointers_target(mapped):
    first, repeat = mapped["200"], mapped["200-1"]
    assert (first["NODE_TYPE"], repeat["NODE_TYPE"]) == ("INTERMEDIARY", "OFFICER")
    for record in (first, repeat):
        assert features(record, "REL_ANCHOR_KEY") == [{"REL_ANCHOR_DOMAIN": "ICIJ_ID", "REL_ANCHOR_KEY": "200"}]
    assert features(repeat, "REL_POINTER_KEY")[0]["REL_POINTER_KEY"] == "100"
