# mapper-ijic

## Overview

The [ijic_mapper.py](ijic_mapper.py) python script converts the ICIJ: International Consortium of Investigative Journalists
csv files to json files ready to load into senzing.  This includes the ...
- Panama Papers 
- Paradise Papers
- Bahamas Leaks
- Offshore Leaks

Loading these watch lists requires additional features and configurations of Senzing. These are contained in the 
[ijic_config_updates.json](ijic_config_updates.json) file and are applied with the [G2ConfigTool.py](G2ConfigTool.py) also contained in this project.

Usage:
```console
python ijic_mapper.py --help
usage: ijic_mapper.py [-h] [-m MAPPING_LIBRARY_PATH] [-i INPUT_PATH]
                      [-o OUTPUT_PATH] [-d DATABASE] [-t NODE_TYPE]
                      [-c ISO_COUNTRY_SIZE] [-s STATISTICS_FILE] [-nr] [-R]

optional arguments:
  -h, --help            show this help message and exit
  -m MAPPING_LIBRARY_PATH, --mapping_library_path MAPPING_LIBRARY_PATH
                        path to the mapping functions library files.
  -i INPUT_PATH, --input_path INPUT_PATH
                        path to the downloaded IJIC csv files.
  -o OUTPUT_PATH, --output_path OUTPUT_PATH
                        path to the output files which default to input file
                        name with a .json extension.
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
4. [Running the dj2json mapper](#Running-the-ijic_mapper)
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
- sets **NAME** and **ADDRESS** to be used for candidates. Normally just their hashes are used to find candidates.  The effect is performance is slightly degraded.
- set **GROUP_ASSOCIATION** feature to be used for candidates.

- set **distinct** off.  Normally this is on to prevent lower strength AKAs to cause matches as only the most distinct names are considered. The effect is more potential false positives.

### Running the ijic_mapper

*Note: It is not necessary to run this mapper!  The source files are free and static so both the input and output file are included in this project.  The code has been included in case any changes are to the mappings are desired or if updates are made to the mapping functions and standards project used by all your data sources.*

```console
python3 ijic_mapper -m <path-to-mapping-library-files> -i /<path-to-ijic-files> -o /<path-to-store-mapped-output-files>
```
- Use the -d parameter if you just want to map one of the 4 databases from IJIC (panama, paradise, bahamas or offshore).
- Use the -t parameter if you just want to map one of the 3 node_types from IJIC (entity, intermediary, or officer).
- Use the -c parameter to change from 3 character to 2 character ISO country codes.
- use the -d parameter if you have renamed the input file so that neither PFA nor HRF is in the file name.
- Use the -s parameter to log the mapping statistics to a file.
- Use the -nr parameter to not create relationships.  This watch list has many disclosed relationships.  It is good to have them, but it loads faster if you turn them off.
- Use the -R parameter if you have downloaded fresh CSV files from the IJIC website.

*Note* The mapping satistics should be reviewed occasionally to determine if there are other values that can be mapped to new features.  Check the UNKNOWN_ID section for values that you may get from other data sources that you would like to make into features.  Most of these values were not mapped because there just aren't enough of them to matter and/or you are not likely to get them from any other data sources. However, DUNS_NUMBER, LEI_NUMBER, and the other new features listed above were found by reviewing these statistics!

### Loading into Senzing

If you use the G2Loader program to load your data, from the /opt/senzing/g2/python directory ...
```console
python3 G2Loader.py -f /<path-to-file>/PFA2_201902282200_F.xml.json
```
The PFA data set currently contains about 2.4 million records and make take a few hours to load depending on your harware.  The HRF file only contains about 70k records and loads in a few minutes. 

If you use the API directly, then you just need to perform an addRecord for each line of the file.

### Mapping other data sources

Watch lists are harder to match simply because often the only data they contain that matches your other data sources are name, partial date of birth, and citizenship or nationality.  Complete address or identifier matches are possible but more rare. For this reason, the following special attributes should be mapped from your internal data sources or search request messages ... 
- **RECORD_TYPE** (valid values are PERSON or ORGANIZATION, only supply if known.)
- **COUNTRY_CODE:** standardized with iso\*.json files included in this package. Simply find any country you can and look it up in either the isoCountries2.json or isoCountries3.json, whichever one you decide to standardize on, and map its iso code to an attribute called country_code. You can prefix with a source word like so ...
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
- **GROUP_ASSOCIATION_ORG_NAME** (Sometimes all you know about a person is who they work for or what groups they are otherwise affiliated with. Consider a contact list that has name, phone number, and company they work for.   Map the company name to the GROUP_ASSOCIATION_ORG_NAME attribute as that may be the only matching attribute to the watch list.
- **PLACE_OF_BIRTH**, **DUNS_NUMBER**, or any of the other additional features listed above. 

### Optional ini file parameter

There is also an ini file change that can benefit watch list matching.  In the pipeline section of the main g2 ini file you use, such as the /opt/senzing/g2/python/G2Module.ini, place the following entry in the pipeline section as show below.

```console
[pipeline]
 NAME_EFEAT_WATCHLIST_MODE=Y
```

This effectively doubles the number of name hashes created which improves the chances of finding a match at the cost of performance.  Consider creating a separate g2 ini file used just for searching and include this parameter.  If you include it during the loading of data, only have it on while loading the watch list as the load time will actually more than double! 

