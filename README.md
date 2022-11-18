# mapper-icij

## Overview

The [icij_mapper.py](icij_mapper.py) python script converts the ICIJ Offshore Leaks database to json files ready to load into Senzing. 

This includes the ...
- Panama Papers
- Paradise Papers
- Bahamas Leaks
- Offshore Leaks
- Pandora Papers (added in 2020)

*In May 2022, ICIJ added additional records to their database and updated their format again.   This mapper will only work
with files dated 05/03/2022 which can be downloaded [here](https://offshoreleaks-data.icij.org/offshoreleaks/csv/full-oldb.20220503.zip)*

***Since the ICIJ data set is static, we have already run this mapper and made the mapped json file available.  You can
download it by clicking here:
[icij_2022.json.zip](https://public-read-access.s3.amazonaws.com/mapped-data-sets/icij-offshore-leaks/icij_2022.json.zip).
You can then unzip it and load it right into Senzing!  But don't forget to add the configuration first as documented below!***

Loading ICIJ data into Senzing requires additional features and configurations. These are contained in the
[icij_config_updates.g2c](icij_config_updates.g2c) file.


Usage:

```console
python icij_mapper.py --help
usage: icij_mapper.py [-h] [-i INPUT_PATH] [-o OUTPUT_FILE] [-l LOG_FILE] [-a]

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT_PATH, --input_path INPUT_PATH
                        path to the downloaded ICIJ csv files
  -o OUTPUT_FILE, --output_file OUTPUT_FILE
                        path and file name for the json output
  -l LOG_FILE, --log_file LOG_FILE
                        optional statistics filename (json format)
  -a, --include_address_nodes
                        include address nodes
```

## Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuring Senzing](#configuring-senzing)
4. [Running the mapper](#running-the-mapper)
5. [Loading into Senzing](#loading-into-senzing)

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

This will step you through the process of adding any data sources, features, attributes and other settings needed to load this data into Senzing.
After each command you will see a status message saying "success" or "already exists".
For instance, if you run the script twice, the second time through they will all say "already exists" which is OK.

### Running the mapper

Download the raw files from: [https://offshoreleaks.icij.org/pages/database](https://offshoreleaks.icij.org/pages/database)

![download page](images/download_page.jpg)

With the addition of the Pandora Papers in November 2020 and again in May 2022, there is now only 1 zip file
 *currently* named **full-oldb-20220503.zip** containing the files listed below:

- nodes-entities.csv
- nodes-intermediaries.csv
- nodes-officers.csv
- nodes-addresses.csv
- nodes-others.csv
- relationships.csv

Unzip the files to a directory of your choice. *(in the example below the csv files were unzipped to /senzing/mappers/mapper-icij/input)*

The mapper will read all the files and create one output file.  Example usage:

```console
python3 icij_mapper.py -i /senzing/mappers/mapper-icij/input -o /senzing/mappers/mapper-icij/output/icij_2022.json
```
- Add the -l --log_file argument to generate a mapping statistics file
- Add the -a --include_address_nodes argument to generate the address nodes as well. *Please note that addresses from these nodes
are mapped to their entities regardless of this setting.*


### Loading into Senzing

If you use the G2Loader program to load your data, from the /opt/senzing/g2/python directory ...

```console
python3 G2Loader.py -f /senzing/mappers/mapper-icij/output/icij_2022.json
```

This data set currently contains about 1.9 million records and make take an hour or more to load depending on your hardware.
