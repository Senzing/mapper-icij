# mapper-icij

## Overview

The [icij_mapper.py](icij_mapper.py) python script converts the ICIJ: International Consortium of Investigative Journalists
csv files to json files ready to load into Senzing.  This includes the ...

- Panama Papers
- Paradise Papers
- Bahamas Leaks
- Offshore Leaks

Loading ICIJ data into Senzing requires additional features and configurations. These are contained in the
[icij_config_updates.g2c](icij_config_updates.g2c) file.

Usage:

```console
python icij_mapper.py --help
usage: icij_mapper.py [-h] [-i INPUT_PATH] [-o OUTPUT_FILE]
                      [-l LOG_FILE] [-d DATABASE]
                      [-t NODE_TYPE] [-R]

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT_PATH, --input_path INPUT_PATH
                        path to the downloaded icij csv files.
  -o OUTPUT_FILE, --output_file OUTPUT_FILE
                        path and file name for the json output.
  -l LOG_FILE, --log_file LOG_FILE
                        optional statistics filename (json format).
  -d DATABASE, --database DATABASE
                        choose: panama, bahamas, paradise, offshore or all,
                        default=all
  -t NODE_TYPE, --node_type NODE_TYPE
                        choose: entity, intermediary, officer or all,
                        default=all
  -R, --reload_csvs     reload from csvs, don't use cached data.
```

## Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuring Senzing](#configuring-senzing)
4. [Running the mapper](#running-the-mapper)
5. [Loading into Senzing](#loading-into-senzing)
6. [Mapping other data sources](#mapping-other-data-sources)

### Prerequisites

- python 3.6 or higher
- Senzing API version 1.13 or higher
- pandas (pip3 install pandas)
- [Senzing/mapper-base](https://github.com/Senzing/mapper-base)

### Installation

Place the the following files on a directory of your choice ...

- [icij_mapper.py](icij_mapper.py)
- [icij_config_updates.g2c](icij_config_updates.g2c)

*Note: Since the mapper-base project referenced above is required by this mapper, it is necessary to place them in a common directory structure like so ...*

```Console
/senzing/mappers/mapper-base
/senzing/mappers/mapper-icij         <--
```

You will also need to set the PYTHONPATH to where the base mapper is as follows ... (assumuing the directory structure above)

```Console
export PYTHONPATH=$PYTHONPATH:/senzing/mappers/mapper-base
```

### Configuring Senzing

*Note:* This only needs to be performed one time! In fact you may want to add these configuration updates to a master configuration file for all your data sources.

From the /opt/senzing/g2/python directory ...

```console
python3 G2ConfigTool.py <path-to-file>/icij_config_updates.g2c
```

This will step you through the process of adding the data sources, entity types, features, attributes and other settings needed to load this watch list data into Senzing. After each command you will see a status message saying "success" or "already exists".  For instance, if you run the script twice, the second time through they will all say "already exists" which is OK.

*Please note the use of ENTITY_TYPE is being deprecated in favor of RECORD_TYPE.  This mapper maps both for backwards compatibility.*

### Running the mapper

Download the raw files from ... [https://offshoreleaks.icij.org/pages/database](https://offshoreleaks.icij.org/pages/database)

There are 4 zip files containing the files listed below. Its best just to unzip them all on the same directory

#### csv_panama_papers.zip

- panama_papers.nodes.address.csv
- panama_papers.nodes.entity.csv
- panama_papers.nodes.intermediary.csv
- panama_papers.nodes.officer.csv
- panama_papers.edges.csv

#### csv_paradise_papers.zip

- paradise_papers.nodes.address.csv
- paradise_papers.nodes.entity.csv
- paradise_papers.nodes.intermediary.csv
- paradise_papers.nodes.officer.csv
- paradise_papers.nodes.other.csv
- paradise_papers.edges.csv

#### csv_bahamas_leaks.zip

- bahamas_leaks.nodes.address.csv
- bahamas_leaks.nodes.entity.csv
- bahamas_leaks.nodes.intermediary.csv
- bahamas_leaks.nodes.officer.csv
- bahamas_leaks.edges.csv

#### csv_offshore_leaks.zip

- offshore_leaks.nodes.address.csv
- offshore_leaks.nodes.entity.csv
- offshore_leaks.nodes.intermediary.csv
- offshore_leaks.nodes.officer.csv
- offshore_leaks.edges.csv

The mapper will read all the files and create one output file.  Example usage:

```console
python3 icij_mapper.py -i ./input -o ./output/icij_2018.json -l icij_stats.json
```

- Add the -d parameter if you just want to map one of the 4 databases from ICIJ (panama, paradise, bahamas or offshore).
- Add the -t parameter if you just want to map one of the 3 node_types from ICIJ (entity, intermediary, or officer).
- Use the -nr parameter to not create relationships.  This watch list has many disclosed relationships.  It is good to have them, but it loads faster if you turn them off.
- Use the -ck parameter if you are using a Senzing version prior to 1.13 and the composite keys will be generated by this mapper.   After version 1.13, the keys are generated automatically.
- Use the -R parameter if you have downloaded fresh csv files from the ICIJ website.

### Loading into Senzing

If you use the G2Loader program to load your data, from the /opt/senzing/g2/python directory ...

```console
python3 G2Loader.py -f /icij_mapper/output/icij_2018.json
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
