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
usage: ijic_mapper.py [-h] [-m MAPPING_LIBRARY_PATH] [-i INPUT_PATH]
                      [-o OUTPUT_FILE] [-d DATABASE] [-t NODE_TYPE]
                      [-c ISO_COUNTRY_SIZE] [-s STATISTICS_FILE] [-nr] [-R]

optional arguments:
  -h, --help            show this help message and exit
  -m MAPPING_LIBRARY_PATH, --mapping_library_path MAPPING_LIBRARY_PATH
                        path to the mapping functions library files.
  -i INPUT_PATH, --input_path INPUT_PATH
                        path to the downloaded IJIC csv files.
  -o OUTPUT_FILE, --output_file OUTPUT_FILE
                        path and file name for the json output.
  -d DATABASE, --database DATABASE
                        choose: panama, bahamas, paradise, offshore or all,
                        default=all
  -t NODE_TYPE, --node_type NODE_TYPE
                        choose: entity, intermediary, officer or all,
                        default=all
  -c ISO_COUNTRY_SIZE, --iso_country_size ISO_COUNTRY_SIZE
                        Choose either 2 or 3, default=3.
  -s STATISTICS_FILE, --statistics_file STATISTICS_FILE
                        optional statistics filename in json format.
  -nr, --no_relationships
                        do not create disclosed realtionships, an attribute
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
7. [Optional ini file parameter](#Optional-ini-file-parameter)

### Prerequisites
- python 3.6 or higher
- pandas (pip3 install pandas)
- Senzing API version 1.7 or higher
- https://github.com/Senzing/mapper-functions

### Installation

Place the the following files on a directory of your choice ...
- [ijic_mapper.py](ijic_mapper.py) 
- [ijic_config_updates.json](ijic_config_updates.json)

*Note: Since the mapper-functions project referenced above is required by this mapper, it is a necessary to place them in a common directory structure.*

### Configuring Senzing

*Note:* This only needs to be performed one time! In fact you may want to add these configuration updates to a master configuration file for all your data sources.

Update the G2ConfigTool.py program file on the /opt/senzing/g2/python directory with this one ... [G2ConfigTool.py](G2ConfigTool.py)

Then from the /opt/senzing/g2/python directory ...
```console
python3 G2ConfigTool.py <path-to-file>/ijic_config_updates.json
```
This will step you through the process of adding the data sources, entity types, features, attributes and other settings needed to load this watch list data into Senzing. After each command you will see a status message saying "success" or "already exists".  For instance, if you run the script twice, the second time through they will all say "already exists" which is OK.

Configuration updates include:
- addDataSource **IJIC**
- addEntityType **PERSON**
- addEntityType **ORGANIZATION**
- add features and attributes for ...
    - **RECORD_TYPE** This helps keep persons and organizations from resolving together.
    - **COUNTRY_CODE** This is a 3 character country code used to improve matching of nationality, citizenship and place of birth.
- Country code is added to the name hasher elements for composite keys.
- Group association type is defaulted to (org) so it does not have to be mapped and will be the same across data sources.
- The following composite keys are added ...
    - CK_NAME_DOB_CNTRY
    - CK_NAME_DOB
    - CK_NAME_CNTRY
    - CK_NAME_ORGNAME

*WARNING:* the following settings are commented out as they affect performance and quality. Only use them if you understand and are OK with the effects.
- sets **NAME**, **ADDRESS** and **GROUP_ASSOCIATION** to be used for candidates. Normally just their hashes are used to find candidates.  The effect is performance is slightly degraded.
- set **distinct** off.  Normally this is on to prevent lower strength AKAs to cause matches as only the most distinct names are considered. The effect is more potential false positives.

### Running the mapper

Download the raw files from ... https://offshoreleaks.icij.org/pages/database

There are 4 zip files containing all of these files. Its best just to unzip them all on the same directory
**csv_panama_papers.zip**
- panama_papers.nodes.address.csv
- panama_papers.nodes.entity.csv
- panama_papers.nodes.intermediary.csv
- panama_papers.nodes.officer.csv
- panama_papers.edges.csv
**csv_paradice_papers.zip**
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
python3 ijic_mapper.py -m ../mapper-functions -i ./input -o ./output/ijic_2018.json
```
- Add the -d parameter if you just want to map one of the 4 databases from IJIC (panama, paradise, bahamas or offshore).
- Add the -t parameter if you just want to map one of the 3 node_types from IJIC (entity, intermediary, or officer).
- Add the -c parameter to change from 3 character to 2 character ISO country codes.
- Use the -s parameter to log the mapping statistics to a file.
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

Watch lists are harder to match simply because often the only data they contain that matches your other data sources are name, partial date of birth, and citizenship or nationality.  Complete address or identifier matches are possible but more rare. For this reason, the following special attributes should be mapped from your internal data sources or search request messages ... 
- **RECORD_TYPE** (valid values are PERSON or ORGANIZATION, only supply if known.)
- **COUNTRY_CODE:** standardized country codes using the mapping_functions project. Simply find any country in your source data and look it up in mapping_standards.json file and map its iso code to an attribute called country_code. You can prefix with a source word like so ...
```console
{
  "NATIONALITY_COUNTRY_CODE": "GER",
  "CITIZENSHIP_COUNTRY_CODE": "USA",
  "PLACE-OF-BIRTH_COUNTRY_CODE": "USA",     <--note the use of dashes not underscores here!
  "ADDRESS_COUNTRY_CODE": "CAN"},
  "PASSPORT_COUNTRY_CODE": "GER"}
}
```
*note: if your source word is an expression, use dashes not underscores so as not to confuse the engine*
- **GROUP_ASSOCIATION_ORG_NAME** (Sometimes all you know about a person is who they work for or what groups they are affiliated with. Consider a contact list that has name, phone number, and company they work for.   Map the company they work for to the GROUP_ASSOCIATION_ORG_NAME attribute as that may be the only matching attribute to the watch list.
- **PLACE_OF_BIRTH**, **DUNS_NUMBER**, or any of the other additional features listed above. 

### Optional ini file parameter

There is also an ini file change that can benefit watch list matching.  In the pipeline section of the main g2 ini file you use, such as the /opt/senzing/g2/python/G2Module.ini, place the following entry in the pipeline section as show below.

```console
[pipeline]
 NAME_EFEAT_WATCHLIST_MODE=Y
```

This effectively doubles the number of name hashes created which improves the chances of finding a match at the cost of performance.  Consider creating a separate g2 ini file used just for searching and include this parameter.  If you include it during the loading of data, only have it on while loading the watch list as the load time will actually more than double! 

