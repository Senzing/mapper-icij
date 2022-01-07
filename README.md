# mapper-icij

## Overview

The [icij_mapper.py](icij_mapper.py) python script converts the ICIJ Offshore Leaks database to json files ready to load into Senzing. 

This includes the ...
- Panama Papers
- Paradise Papers
- Bahamas Leaks
- Offshore Leaks
- Pandora Papers (added in 2020)

Loading ICIJ data into Senzing requires additional features and configurations. These are contained in the
[icij_config_updates.g2c](icij_config_updates.g2c) file.

***Since the ICIJ data set is static, we have already run this mapper and made the mapped json file available 
[here](https://public-read-access.s3.amazonaws.com/mapped-data-sets/icij-panama-papers/icij_2021.json.zip).
You can simply download this file, unzip it and load it right into Senzing!  But don't forget to add the configuration 
first as documented below!***

Usage:

```console
python icij_mapper.py --help
usage: icij_mapper.py [-h] [-i INPUT_PATH] [-o OUTPUT_FILE] [-l LOG_FILE]

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT_PATH, --input_path INPUT_PATH
                        path to the downloaded ICIJ csv files
  -o OUTPUT_FILE, --output_file OUTPUT_FILE
                        path and file name for the json output
  -l LOG_FILE, --log_file LOG_FILE
                        optional statistics filename (json format)
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
- Senzing API version 2.1 or higher
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

Download the raw files from: [https://offshoreleaks.icij.org/pages/database](https://offshoreleaks.icij.org/pages/database)

With the addition of the Pandora Papers in November 2020, there is now only 1 zip file *currently* named **full-oldb-20211202.zip** containing the files 
listed below:

- nodes-entities.csv
- nodes-intermediaries.csv
- nodes-officers.csv
- nodes-addresses.csv
- nodes-others.csv
- relationships.csv

The mapper will read all the files and create one output file.  Example usage:

```console
python3 icij_mapper.py -i /icij_mapper/input -o /icij_mapper/output/icij_2020.json -l icij_stats.json
```
*where /icij_mapper/input/ is where the unziped csv files are located*

### Loading into Senzing

If you use the G2Loader program to load your data, from the /opt/senzing/g2/python directory ...

```console
python3 G2Loader.py -f /icij_mapper/output/icij_2020.json
```

This data set currently contains about 1.9 million records and make take an hour or more to load depending on your hardware.
