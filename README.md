# mapper-ijic

## Overview

The [ijic_mapper.py](ijic_mapper.py) python script converts the ICIJ: International Consortium of Investigative Journalists
csv files to json files ready to load into senzing.  This includes the ...
- Panama Papers 
- Paradise Papers
- Bahamas Leaks
- Offshore Leaks

Loading IJIC data into Senzing requires additional features and configurations. These are contained in the 
[ijic_config_updates.json](ijic_config_updates.json) file and are applied with the [G2ConfigTool.py](G2ConfigTool.py) also contained in this project.

Usage:
```console
python ijic_mapper.py --help
usage: ijic_mapper.py [-h] [-i INPUT_PATH] [-o OUTPUT_FILE]
                      [-b BASE_LIBRARY_PATH] [-l LOG_FILE] [-d DATABASE]
                      [-t NODE_TYPE] [-nr] [-R]

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT_PATH, --input_path INPUT_PATH
                        path to the downloaded IJIC csv files.
  -o OUTPUT_FILE, --output_file OUTPUT_FILE
                        path and file name for the json output.
  -b BASE_LIBRARY_PATH, --base_library_path BASE_LIBRARY_PATH
                        path to the base library files.
  -l LOG_FILE, --log_file LOG_FILE
                        optional statistics filename (json format).
  -d DATABASE, --database DATABASE
                        choose: panama, bahamas, paradise, offshore or all,
                        default=all
  -t NODE_TYPE, --node_type NODE_TYPE
                        choose: entity, intermediary, officer or all,
                        default=all
  -nr, --no_relationships
                        do not create disclosed relationships, an attribute
                        will still be stored
  -R, --reload_csvs     reload from csvs, don't use cached data.
```

## Contents

1. [Prerequisites](#Prerequisites)
2. [Installation](#Installation)
3. [Configuring Senzing](#Configuring-Senzing)
4. [Running the mapper](#Running-the-mapper)
5. [Loading into Senzing](#Loading-into-Senzing)
6. [Mapping other data sources](#Mapping-other-data-sources)

### Prerequisites
- python 3.6 or higher
- pandas (pip3 install pandas)
- Senzing API version 1.7 or higher
- https://github.com/Senzing/mapper-base

### Installation

Place the the following files on a directory of your choice ...
- [ijic_mapper.py](ijic_mapper.py) 
- [ijic_config_updates.json](ijic_config_updates.json)

*Note: Since the mapper-base project referenced above is required by this mapper, it is necessary to place them in a common directory structure like so ...*
```Console
/senzing/mappers/mapper-base
/senzing/mappers/mapper-ijic         <--
```

### Configuring Senzing

*Note:* This only needs to be performed one time! In fact you may want to add these configuration updates to a master configuration file for all your data sources.

**If you are on version G2 API version 1.10 or prior**, update the G2ConfigTool.py program file on the /opt/senzing/g2/python directory with this one ... [G2ConfigTool.py](G2ConfigTool.py)

Then from the /opt/senzing/g2/python directory ...
```console
python3 G2ConfigTool.py <path-to-file>/ijic_config_updates.json
```
This will step you through the process of adding the data sources, entity types, features, attributes and other settings needed to load this watch list data into Senzing. After each command you will see a status message saying "success" or "already exists".  For instance, if you run the script twice, the second time through they will all say "already exists" which is OK.

Configuration updates include:
- addDataSource **IJIC**
- addEntityType **PERSON**
- addEntityType **ORGANIZATION**

### Running the mapper

Download the raw files from ... https://offshoreleaks.icij.org/pages/database

There are 4 zip files containing the files listed below. Its best just to unzip them all on the same directory

**csv_panama_papers.zip**
- panama_papers.nodes.address.csv
- panama_papers.nodes.entity.csv
- panama_papers.nodes.intermediary.csv
- panama_papers.nodes.officer.csv
- panama_papers.edges.csv

**csv_paradise_papers.zip**
- paradise_papers.nodes.address.csv
- paradise_papers.nodes.entity.csv
- paradise_papers.nodes.intermediary.csv
- paradise_papers.nodes.officer.csv
- paradise_papers.nodes.other.csv
- paradise_papers.edges.csv

**csv_bahamas_leaks.zip**
- bahamas_leaks.nodes.address.csv
- bahamas_leaks.nodes.entity.csv
- bahamas_leaks.nodes.intermediary.csv
- bahamas_leaks.nodes.officer.csv
- bahamas_leaks.edges.csv

**csv_offshore_leaks.zip**
- offshore_leaks.nodes.address.csv
- offshore_leaks.nodes.entity.csv
- offshore_leaks.nodes.intermediary.csv
- offshore_leaks.nodes.officer.csv
- offshore_leaks.edges.csv

The mapper will read all the files and create one output file.  Example usage:
```console
python3 ijic_mapper.py -i ./input -o ./output/ijic_2018.json -b ../mapper-base -l ijic_stats.json
```
- Add the -d parameter if you just want to map one of the 4 databases from IJIC (panama, paradise, bahamas or offshore).
- Add the -t parameter if you just want to map one of the 3 node_types from IJIC (entity, intermediary, or officer).
- Use the -nr parameter to not create relationships.  This watch list has many disclosed relationships.  It is good to have them, but it loads faster if you turn them off.
- Use the -R parameter if you have downloaded fresh csv files from the IJIC website.

### Loading into Senzing

If you use the G2Loader program to load your data, from the /opt/senzing/g2/python directory ...
```console
python3 G2Loader.py -f /ijic_mapper/output/ijic_2018.json
```
This data set currently contains about 1.5 million records and make take a few hours to load depending on your harware.
If you use the API directly, then you just need to perform an addRecord() for each line of the file.

### Mapping other data sources

Watch lists are harder to match simply because often the only data they contain that matches your other data sources are name, partial date of birth, and citizenship or nationality.  Complete address or identifier matches are possible but more rare. Likewise, employer names and other group affiliations can also help match watch lists.  Look for and map these features in your source data ...
- CITIZENSHIP
- NATIONALITY
- ADDRESS_COUNTRY in addresses
- PASSPORT_COUNTRY and other identifier countries
- GROUP_ASSOCIATION_ORG_NAME (employers and other group affiliations)

