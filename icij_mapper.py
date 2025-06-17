#! /usr/bin/env python3

import sys
import os
import argparse
import signal
import time
import json
import pandas
import sqlite3
import random

# --try to import the base mapper library and variants
try:
    import base_mapper
except:
    print("")
    print("Please export PYTHONPATH=$PYTHONPATH:<path to mapper-base project>")
    print("")
    sys.exit(1)
baseLibrary = base_mapper.base_library(
    os.path.abspath(base_mapper.__file__).replace(
        "base_mapper.py", "base_variants.json"
    )
)
if not baseLibrary.initialized:
    sys.exit(1)


# ----------------------------------------
def signal_handler(signal, frame):
    print("USER INTERRUPT! Shutting down ... (please wait)")
    global shutDown
    shutDown = True


# ----------------------------------------
def updateStat(cat1, cat2, example=None):
    if cat1 not in statPack:
        statPack[cat1] = {}
    if cat2 not in statPack[cat1]:
        statPack[cat1][cat2] = {}
        statPack[cat1][cat2]["count"] = 0

    statPack[cat1][cat2]["count"] += 1
    if example:
        if "examples" not in statPack[cat1][cat2]:
            statPack[cat1][cat2]["examples"] = []
        if example not in statPack[cat1][cat2]["examples"]:
            if len(statPack[cat1][cat2]["examples"]) < 5:
                statPack[cat1][cat2]["examples"].append(example)
            else:
                randomSampleI = random.randint(2, 4)
                statPack[cat1][cat2]["examples"][randomSampleI] = example


# ----------------------------------------
def csv2db():
    """load database"""
    for fileDict in inputFiles:
        dbObj = conn.cursor()
        dbCursor = dbObj.execute(
            "select name from sqlite_master where type='table' AND name='%s'"
            % fileDict["tableName"]
        )
        dbRow = dbCursor.fetchone()
        if not dbRow:

            # note: in dec 2020, ICIJ released the Pandora Papers and went to a single database - 1 set of csv files for all
            #  the _start and _end fields in the edges table used to refer to the node_id in the node tables
            #  now they refer to the _id field in the node tables

            # note: in may 2022, ICIJ released new data and changed format again
            # Now all edges contain the sourceID value related to the project they belong to.
            # We removed the _id columns, and kept only node_id columns to link between nodes and relationships.
            # Example to merge Officers and Entities nodes:
            # nodes-officers.csv node_id column <-> relationships.csv node_id_start column <-> relationships.csv node_id_end column <-> nodes-entities.csv node_id column

            fileDict["fileName"] = (
                inputPath
                + (os.path.sep if inputPath[-1:] != os.path.sep else "")
                + fileDict["fileName"]
            )
            print("loading %s ..." % fileDict["fileName"])
            df = pandas.read_csv(
                fileDict["fileName"], low_memory=False, encoding="utf-8", quotechar='"'
            )
            df.to_sql(fileDict["tableName"], conn, if_exists="replace")
            if fileDict["nodeType"] != "edges":
                conn.cursor().execute(
                    "create index ix_%s on %s (node_id)"
                    % (fileDict["tableName"], fileDict["tableName"])
                )
            else:

                conn.cursor().execute(
                    "create index ix_%s1 on %s (node_id_start)"
                    % (fileDict["tableName"], fileDict["tableName"])
                )

                sql = "create view %s_view as " % (fileDict["nodeDatabase"] + "_edges",)
                sql += "select  "
                sql += " a.node_id_start, "
                sql += " case when b.node_id is null then "
                sql += "  case when c.node_id is null then "
                sql += "   case when d.node_id is null then "
                sql += "    case when e.node_id is null then null "
                sql += "     else e.node_id end "
                sql += "    else d.node_id end "
                sql += "   else c.node_id end "
                sql += "  else b.node_id end as node1_id, "
                sql += " case when b.node_id is null then "
                sql += "  case when c.node_id is null then "
                sql += "   case when d.node_id is null then "
                sql += "    case when e.node_id is null then null "
                sql += "     else 'address' end "
                sql += "    else 'officer' end "
                sql += "   else 'intermediary' end "
                sql += "  else 'entity' end as node1_type, "
                sql += " case when b.node_id is null then "
                sql += "  case when c.node_id is null then "
                sql += "   case when d.node_id is null then "
                sql += "    case when e.node_id is null then null "
                sql += "     else case when e.name is null then e.address else e.name end end "
                sql += "    else d.name end "
                sql += "   else c.name end "
                sql += "  else b.name end as node1_desc, "
                sql += " a.rel_type, "
                sql += " a.link, "
                sql += " a.node_id_end, "
                sql += " case when f.node_id is null then "
                sql += "  case when g.node_id is null then "
                sql += "   case when h.node_id is null then "
                sql += "    case when i.node_id is null then null "
                sql += "     else i.node_id end "
                sql += "    else h.node_id end "
                sql += "   else g.node_id end "
                sql += "  else f.node_id end as node2_id, "
                sql += " case when f.node_id is null then "
                sql += "  case when g.node_id is null then "
                sql += "   case when h.node_id is null then "
                sql += "    case when i.node_id is null then null "
                sql += "     else 'address' end "
                sql += "    else 'officer' end "
                sql += "   else 'intermediary' end "
                sql += "  else 'entity' end as node2_type, "
                sql += " case when f.node_id is null then "
                sql += "  case when g.node_id is null then "
                sql += "   case when h.node_id is null then "
                sql += "    case when i.node_id is null then null "
                sql += "     else case when i.name is null then i.address else i.name end end "
                sql += "    else h.name end "
                sql += "   else g.name end "
                sql += "  else f.name end as node2_desc, "
                sql += " a.start_date, "
                sql += " a.end_date "
                sql += "from %s a " % (fileDict["nodeDatabase"] + "_edges",)
                sql += "left join %s b on b.node_id = a.node_id_start " % (
                    fileDict["nodeDatabase"] + "_entity",
                )
                sql += "left join %s c on c.node_id = a.node_id_start " % (
                    fileDict["nodeDatabase"] + "_intermediary",
                )
                sql += "left join %s d on d.node_id = a.node_id_start " % (
                    fileDict["nodeDatabase"] + "_officer",
                )
                sql += "left join %s e on e.node_id = a.node_id_start " % (
                    fileDict["nodeDatabase"] + "_address",
                )
                sql += "left join %s f on f.node_id = a.node_id_end " % (
                    fileDict["nodeDatabase"] + "_entity",
                )
                sql += "left join %s g on g.node_id = a.node_id_end " % (
                    fileDict["nodeDatabase"] + "_intermediary",
                )
                sql += "left join %s h on h.node_id = a.node_id_end " % (
                    fileDict["nodeDatabase"] + "_officer",
                )
                sql += "left join %s i on i.node_id = a.node_id_end " % (
                    fileDict["nodeDatabase"] + "_address",
                )
                conn.cursor().execute(sql)


# ----------------------------------------
def processTable(fileDict):

    nodeDatabase = fileDict["nodeDatabase"]
    nodeType = fileDict["nodeType"].upper()
    tableName = fileDict["tableName"]

    # --these aren't entities
    if nodeType == "EDGES":
        return 0
    if nodeType == "ADDRESS" and not include_address_nodes:
        return 0

    print("")
    print("processing %s ..." % tableName)

    # --process the records
    dbObj = conn.cursor()
    dbCursor = dbObj.execute("select * from " + tableName)
    dbHeader = [col[0] for col in dbObj.description]
    dbRow = dbCursor.fetchone()
    rowCount = 0
    while dbRow:
        rowCount += 1
        nodeRecord = dict(zip(dbHeader, dbRow))
        jsonData = node2Json(nodeRecord, nodeDatabase, nodeType)
        msg = json.dumps(jsonData)

        try:
            outputFileHandle.write(msg + "\n")
        except IOError as err:
            print("")
            print("Could not write to %s" % outputFileName)
            print(" %s" % err)
            print("")
            global shutDown
            shutDown = True

        if shutDown:
            break

        dbRow = dbCursor.fetchone()
        if rowCount % progressInterval == 0 or not dbRow:
            print(
                " %s %s written%s"
                % (rowCount, tableName, ", complete!" if not dbRow else "")
            )

    # --return error if dd not complete
    return shutDown


# ----------------------------------------
def node2Json(nodeRecord, nodeDatabase, nodeType):
    """map node to json structure"""

    # support for duplicate nodes
    # they are the same real entity, just of a different type as in entity vs intermediary
    node_id = str(nodeRecord["node_id"])
    if node_id in node_cache:
        node_cache[node_id] += 1
        node_id = f"{node_id}-{node_cache[node_id]}"
    else:
        node_cache[node_id] = 0

    # --set the data source
    jsonData = {}
    jsonData["DATA_SOURCE"] = "ICIJ"
    jsonData["RECORD_ID"] = node_id

    entityName = nodeRecord.get("name", "")
    entityAddress = nodeRecord.get("address", "")

    # --the nodes files have a field for this, the address file doesn't
    node_source = nodeRecord.get("sourceID", nodeDatabase)

    # --not all officers are actually people!
    if nodeType.upper() == "OFFICER" and not baseLibrary.isCompanyName(entityName):
        jsonData["RECORD_TYPE"] = "PERSON"
        jsonData["PRIMARY_NAME_FULL"] = entityName
    elif nodeType.upper() == "ADDRESS":
        jsonData["RECORD_TYPE"] = "ADDRESS"
        # address nodes sometimes have the address in the name field
        if entityName and not entityAddress:
            entityAddress = entityName

    else:
        jsonData["RECORD_TYPE"] = "ORGANIZATION"
        jsonData["PRIMARY_NAME_ORG"] = entityName
    jsonData["ICIJ_SOURCE"] = node_source
    jsonData["NODE_TYPE"] = nodeType

    updateStat("SOURCE", node_source)
    updateStat("NODE_TYPE", nodeType.upper())

    countryList = []
    if "jurisdiction" in nodeRecord and nodeRecord["jurisdiction"]:
        jsonData["Jurisdiction"] = nodeRecord["jurisdiction"]
        countryList.append({"COUNTRY_OF_ASSOCIATION": nodeRecord["jurisdiction"]})
    if "country_codes" in nodeRecord and nodeRecord["country_codes"]:
        country_links = []
        for linkedCountry in nodeRecord["country_codes"].split(";"):
            country_links.append(linkedCountry)
            countryList.append({"COUNTRY_OF_ASSOCIATION": linkedCountry})
        nodeRecord["Linked to"] = " | ".join(country_links)
    if countryList:
        jsonData["COUNTRIES"] = countryList

    if "status" in nodeRecord and nodeRecord["status"]:  # --officers don't have status
        jsonData["Status"] = nodeRecord["status"]

    # --only entities have these
    if "company_type" in nodeRecord and nodeRecord["company_type"]:
        jsonData["COMPANY_TYPE"] = nodeRecord["company_type"]
    if "incorporation_date" in nodeRecord and nodeRecord["incorporation_date"]:
        jsonData["INCORPORATED"] = nodeRecord["incorporation_date"]
    if "inactivation_date" in nodeRecord and nodeRecord["inactivation_date"]:
        jsonData["INACTIVATED"] = nodeRecord["inactivation_date"]
    if "struck_off_date" in nodeRecord and nodeRecord["struck_off_date"]:
        jsonData["STRUCK_OFF"] = nodeRecord["struck_off_date"]
    if "note" in nodeRecord and nodeRecord["note"]:
        jsonData["NOTES"] = nodeRecord["note"]

    # --add the anchor so that others can relate to this node
    jsonData["REL_ANCHOR_DOMAIN"] = "ICIJ_ID"
    jsonData["REL_ANCHOR_KEY"] = jsonData["RECORD_ID"]

    # --map related nodes as addresses, group associations and disclosed relationships
    relPointerList = []
    groupAssociationList = []
    addressList = []
    if entityAddress:
        if jsonData["RECORD_TYPE"] == "PERSON":
            addressList.append({"ADDR_TYPE": "PRIMARY", "ADDR_FULL": entityAddress})
        else:
            addressList.append({"ADDR_TYPE": "BUSINESS", "ADDR_FULL": entityAddress})

    edgeObj = conn.cursor()
    edgeSql = f"select * from {nodeDatabase}_edges_view where node_id_start = {nodeRecord['node_id']}"
    edgeCursor = edgeObj.execute(edgeSql)
    edgeHeader = [col[0] for col in edgeObj.description]
    edgeRow = edgeCursor.fetchone()
    while edgeRow:
        edgeRecord = dict(zip(edgeHeader, edgeRow))

        if edgeRecord["link"]:  # --fix long usage types
            if len(edgeRecord["link"]) > 50:
                updateStat("TRUNCATED_LINKS", edgeRecord["link"])
                if ";" in edgeRecord["link"]:
                    edgeRecord["link"] = "MULTIPLE USE"
                else:
                    edgeRecord["link"] = edgeRecord["link"][0:50]

        # --map the relationship if not and address unless including them as nodes
        if edgeRecord["node2_type"] != "address" or include_address_nodes:
            relPointerRecord = {}
            relPointerRecord["REL_POINTER_DOMAIN"] = "ICIJ_ID"
            relPointerRecord["REL_POINTER_KEY"] = edgeRecord["node2_id"]
            relPointerRecord["REL_POINTER_ROLE"] = edgeRecord["link"]
            if edgeRecord["start_date"]:
                relPointerRecord["REL_POINTER_FROM_DATE"] = edgeRecord["start_date"]
            if edgeRecord["end_date"]:
                relPointerRecord["REL_POINTER_THRU_DATE"] = edgeRecord["end_date"]
            relPointerList.append(relPointerRecord)

        # --map the related node as an address if it is one
        if edgeRecord["node2_type"] == "address":
            if edgeRecord["node2_desc"] not in addressList:
                addrType = (
                    edgeRecord["link"].upper().replace(" ADDRESS", "")[0:50]
                    if edgeRecord["link"]
                    else "ADDRESS"
                )
                if jsonData["RECORD_TYPE"] == "ORGANIZATION" and (
                    "REGISTERED" in addrType or "BUSINESS" in addrType
                ):
                    addrType = "BUSINESS"
                addressRecord = {
                    "ADDR_TYPE": addrType,
                    "ADDR_FULL": edgeRecord["node2_desc"],
                }
                if addressRecord not in addressList:
                    addressList.append(addressRecord)

        # --map the related node as a group name so can be used for matching if its an officer pointing to an entity
        if jsonData["RECORD_TYPE"] == "PERSON" and edgeRecord["node2_type"] == "entity":
            if edgeRecord["node2_type"] == "entity":  # --should always be true
                groupAssociationRecord = {
                    "GROUP_ASSOCIATION_ORG_NAME": edgeRecord["node2_desc"]
                }
                if groupAssociationRecord not in groupAssociationList:
                    groupAssociationList.append(groupAssociationRecord)

        edgeRow = edgeCursor.fetchone()

    if addressList:
        jsonData["ADDRESSES"] = addressList

    if groupAssociationList and jsonData["RECORD_TYPE"] == "PERSON":
        jsonData["GROUP_ASSOCIATIONS"] = groupAssociationList

    if relPointerList:
        jsonData["RELATIONSHIPS"] = relPointerList

    node_type = jsonData.get("NODE_TYPE", "UNKNOWN")
    for key1 in jsonData.keys():
        if isinstance(jsonData[key1], list):
            for subrecord in jsonData[key1]:
                for key2 in subrecord.keys():
                    updateStat(node_type, key2, subrecord[key2])
        else:
            updateStat(node_type, key1, jsonData[key1])

    return jsonData


# ----------------------------------------
if __name__ == "__main__":
    appPath = os.path.dirname(os.path.abspath(sys.argv[0]))

    global shutDown
    shutDown = False
    signal.signal(signal.SIGINT, signal_handler)
    procStartTime = time.time()
    progressInterval = 10000

    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        "-i",
        "--input_path",
        default=os.getenv("input_path".upper(), None),
        type=str,
        help="path to the downloaded ICIJ csv files",
    )
    argparser.add_argument(
        "-o",
        "--output_file",
        default=os.getenv("output_file".upper(), None),
        type=str,
        help="path and file name for the json output",
    )
    argparser.add_argument(
        "-l",
        "--log_file",
        default=os.getenv("log_file".upper(), None),
        type=str,
        help="optional statistics filename (json format)",
    )
    argparser.add_argument(
        "-a",
        "--include_address_nodes",
        dest="include_address_nodes",
        action="store_true",
        default=False,
        help="include address nodes",
    )
    args = argparser.parse_args()
    inputPath = args.input_path
    outputFileName = args.output_file
    logFile = args.log_file
    include_address_nodes = args.include_address_nodes

    if not (inputPath):
        print("")
        print("Please supply the path to the downloaded ICIJ csv files.")
        print("")
        sys.exit(1)

    if not (outputFileName):
        print("")
        print("Please supply an output file name.")
        print("")
        sys.exit(1)

    # --open output file
    try:
        outputFileHandle = open(outputFileName, "w", encoding="utf-8")
    except IOError as err:
        print("")
        print("Could not open output file %s for writing" % outputFileName)
        print(" %s" % err)
        print("")
        sys.exit(1)

    # --register the expected files
    inputFiles = []
    inputFiles.append(
        {"fileName": "nodes-entities.csv", "nodeDatabase": "icij", "nodeType": "entity"}
    )
    inputFiles.append(
        {
            "fileName": "nodes-intermediaries.csv",
            "nodeDatabase": "icij",
            "nodeType": "intermediary",
        }
    )
    inputFiles.append(
        {
            "fileName": "nodes-officers.csv",
            "nodeDatabase": "icij",
            "nodeType": "officer",
        }
    )
    inputFiles.append(
        {
            "fileName": "nodes-addresses.csv",
            "nodeDatabase": "icij",
            "nodeType": "address",
        }
    )
    inputFiles.append(
        {"fileName": "nodes-others.csv", "nodeDatabase": "icij", "nodeType": "other"}
    )
    inputFiles.append(
        {"fileName": "relationships.csv", "nodeDatabase": "icij", "nodeType": "edges"}
    )
    # --create a table name for each file
    for i in range(len(inputFiles)):
        inputFiles[i]["tableName"] = (
            inputFiles[i]["nodeDatabase"] + "_" + inputFiles[i]["nodeType"]
        )

    # --open database connection and load from csv if first time
    dbname = (
        inputPath + (os.path.sep if inputPath[-1:] != os.path.sep else "") + "icij2.db"
    )
    dbExists = os.path.exists(dbname)
    if dbExists:
        os.remove(dbname)
    conn = sqlite3.connect(dbname)
    csv2db()

    # --initialize the statpack
    statPack = {}
    node_cache = {}  # to support duplicate node IDs

    # --process each table
    for fileDict in inputFiles:
        processTable(fileDict)
        if shutDown:
            break

    outputFileHandle.close()

    # --write statistics file
    if logFile:
        print("")
        statPack["BASE_LIBRARY"] = baseLibrary.statPack
        with open(logFile, "w") as outfile:
            json.dump(statPack, outfile, indent=4, sort_keys=True)
        print("Mapping stats written to %s" % logFile)

    print("")
    elapsedMins = round((time.time() - procStartTime) / 60, 1)
    if shutDown == 0:
        print("Process completed successfully in %s minutes!" % elapsedMins)
    else:
        print("Process aborted after %s minutes!" % elapsedMins)
    print("")

    sys.exit(0)
