#! /usr/bin/env python3

import sys
import os
import argparse
import signal
import time
from datetime import datetime, timedelta
import json
import re
import pandas
import sqlite3

#--import the base mapper library and variants
try: 
    import base_mapper
except: 
    print('')
    print('Please export PYTHONPATH=$PYTHONPATH:<path to mapper-base project>')
    print('')
    sys.exit(1)
baseLibrary = base_mapper.base_library(os.path.abspath(base_mapper.__file__).replace('base_mapper.py','base_variants.json'))
if not baseLibrary.initialized:
    sys.exit(1)

#----------------------------------------
def pause(question='PRESS ENTER TO CONTINUE ...'):
    """ pause for debug purposes """
    try: response = input(question)
    except KeyboardInterrupt:
        response = None
        global shutDown
        shutDown = True
    return response

#----------------------------------------
def signal_handler(signal, frame):
    print('USER INTERUPT! Shutting down ... (please wait)')
    global shutDown
    shutDown = True
    return
        
#----------------------------------------
def updateStat(cat1, cat2, example = None):
    if cat1 not in statPack:
        statPack[cat1] = {}
    if cat2 not in statPack[cat1]:
        statPack[cat1][cat2] = {}
        statPack[cat1][cat2]['count'] = 0

    statPack[cat1][cat2]['count'] += 1
    if example:
        if 'examples' not in statPack[cat1][cat2]:
            statPack[cat1][cat2]['examples'] = []
        if example not in statPack[cat1][cat2]['examples']:
            if len(statPack[cat1][cat2]['examples']) < 5:
                statPack[cat1][cat2]['examples'].append(example)
            else:
                randomSampleI = random.randint(2,4)
                statPack[cat1][cat2]['examples'][randomSampleI] = example
    return

#----------------------------------------
def csv2db():
    ''' load database '''
    for fileDict in inputFiles:
        if fileDict['nodeDatabase'].upper() == nodeDatabase.upper() or nodeDatabase.upper() == 'ALL':
            dbObj = conn.cursor()
            dbCursor = dbObj.execute("select name from sqlite_master where type='table' AND name='%s'" % fileDict['tableName'])
            dbRow = dbCursor.fetchone()
            if not dbRow:
                fileDict['fileName'] = inputPath + (os.path.sep if inputPath[-1:] != os.path.sep else '') + fileDict['fileName']
                print('loading %s ...' % fileDict['fileName'])
                df = pandas.read_csv(fileDict['fileName'], low_memory=False, encoding="latin-1", quotechar='"')
                df.to_sql(fileDict['tableName'], conn, if_exists="replace")
                if fileDict['nodeType'] != 'edges':
                    conn.cursor().execute('create unique index ix_%s on %s (node_id, sourceID)' % (fileDict['tableName'], fileDict['tableName']))
                else:
                    if fileDict['nodeDatabase'] in ['bahamas']:
                        relTypeField = 'rel_type'
                        node1Field = 'node_1'
                        node2Field = 'node_2'
                    else:
                        relTypeField = 'TYPE'
                        node1Field = 'START_ID'
                        node2Field = 'END_ID'

                    conn.cursor().execute('create index ix_%s1 on %s (%s, %s)' % (fileDict['tableName'], fileDict['tableName'], node1Field, node2Field))
                    conn.cursor().execute('create index ix_%s2 on %s (%s, %s)' % (fileDict['tableName'], fileDict['tableName'], node2Field, node1Field))
                    
                    sql = "create view %s_view as " % (fileDict['nodeDatabase'] + '_edges',)
                    sql += "select  "
                    sql += " a.%s as node_1, " % (node1Field,)
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
                    sql += "     else e.address end " 
                    sql += "    else d.name end "
                    sql += "   else c.name end "
                    sql += "  else b.name end as node1_desc, "
                    sql += " a.%s as rel_type, " % (relTypeField,)
                    sql += " a.%s as node_2, " % (node2Field)
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
                    sql += "     else i.address end " 
                    sql += "    else h.name end "
                    sql += "   else g.name end "
                    sql += "  else f.name end as node2_desc, "
                    sql += " a.start_date, "
                    sql += " a.end_date "
                    sql += "from %s a "  % (fileDict['nodeDatabase'] + '_edges',)
                    sql += "left join %s b on b.node_id = a.%s "  % (fileDict['nodeDatabase'] + '_entity', node1Field)
                    sql += "left join %s c on c.node_id = a.%s "  % (fileDict['nodeDatabase'] + '_intermediary', node1Field)
                    sql += "left join %s d on d.node_id = a.%s "  % (fileDict['nodeDatabase'] + '_officer', node1Field)
                    sql += "left join %s e on e.node_id = a.%s "  % (fileDict['nodeDatabase'] + '_address', node1Field) 
                    sql += "left join %s f on f.node_id = a.%s "  % (fileDict['nodeDatabase'] + '_entity', node2Field)
                    sql += "left join %s g on g.node_id = a.%s "  % (fileDict['nodeDatabase'] + '_intermediary', node2Field)
                    sql += "left join %s h on h.node_id = a.%s "  % (fileDict['nodeDatabase'] + '_officer', node2Field)
                    sql += "left join %s i on i.node_id = a.%s "  % (fileDict['nodeDatabase'] + '_address', node2Field)
                    conn.cursor().execute(sql)

    return

#----------------------------------------
def processTable(fileDict):

    nodeDatabase = fileDict['nodeDatabase']
    nodeType = fileDict['nodeType']
    tableName = fileDict['tableName']
    
    #--these aren't entities
    if nodeType in ['edges', 'address', 'other']:
        return 0

    print('')
    print('processing %s ...' % tableName)
    
    #--process the records
    dbObj = conn.cursor()
    dbCursor = dbObj.execute('select * from ' + tableName)
    dbHeader = [col[0] for col in dbObj.description]
    dbRow = dbCursor.fetchone()
    rowCount = 0
    while dbRow:
        rowCount += 1
        nodeRecord = dict(zip(dbHeader, dbRow))
        jsonData = node2Json(tableName, nodeRecord, nodeDatabase, nodeType)
        msg = json.dumps(jsonData, ensure_ascii=False)
        #if len(msg) > 10000:
        #    print(msg)
        #    pause()

        try: outputFileHandle.write(msg + '\n')
        except IOError as err:
            print('')
            print('Could not write to %s' % outputFileName)
            print(' %s' % err)
            print('')
            global shutDown
            shutDown = True

        if shutDown:
            break

        dbRow = dbCursor.fetchone()
        if rowCount % progressInterval == 0 or not dbRow:
            print(' %s %s written%s' % (rowCount, tableName, ', complete!' if not dbRow else ''))

    #--return error if dd not complete
    return shutDown

#----------------------------------------
def node2Json(tableName, nodeRecord, nodeDatabase, nodeType):
    ''' map node to json structure '''
    
    #--set the data source
    jsonData = {}
    jsonData['DATA_SOURCE'] = 'IJIC' + '-' + nodeDatabase.upper()
    jsonData['RECORD_ID'] = str(nodeRecord['node_id'])

    #--cleanup the name ("the bearer" is like "unknown")
    entityName = nodeRecord['name'] if 'name' in nodeRecord and nodeRecord['name'] else ''
    if 'bearer' in entityName.lower():
        jsonData['Name'] = entityName
        entityName = ''

    #--not all officers are actually people!
    if nodeType.upper() == 'OFFICER' and not baseLibrary.isCompanyName(entityName):
        jsonData['ENTITY_TYPE'] = 'PERSON'
        jsonData['PRIMARY_NAME_FULL'] = entityName
    else:
        jsonData['ENTITY_TYPE'] = 'ORGANIZATION'
        jsonData['PRIMARY_NAME_ORG'] = entityName
    jsonData['RECORD_TYPE'] = jsonData['ENTITY_TYPE']
    jsonData['Node_type'] = nodeType.upper()

    updateStat('DATA_SOURCE', jsonData['DATA_SOURCE'])
    updateStat('ENTITY_TYPE', jsonData['ENTITY_TYPE'])
    updateStat('NODE_TYPE', nodeType.upper())

    if 'jurisdiction' in nodeRecord and nodeRecord['jurisdiction']:
        jsonData['Jurisdiction_country'] = nodeRecord['jurisdiction']
    if 'jurisdiction_description' in nodeRecord and nodeRecord['jurisdiction_description']:
        jsonData['Jurisdiction_description'] = nodeRecord['jurisdiction_description']

    if 'country_codes' in nodeRecord and nodeRecord['country_codes']:
        instance = 0
        for linkedCountry in nodeRecord['country_codes'].split(';'):
            jsonData['Linked_country%s' % (('_' + str(instance)) if instance > 0 else '')] = linkedCountry
            instance += 1
    if 'countries' in nodeRecord and nodeRecord['countries']:
        jsonData['Linked_country_names'] = nodeRecord['countries']


    if 'status' in nodeRecord and nodeRecord['status']:  #--officers don't have status
        jsonData['Status'] = nodeRecord['status']

    #--only entities have these
    if 'company_type' in nodeRecord and nodeRecord['company_type']:
        jsonData['Company type'] = nodeRecord['company_type']
    if 'incorporation_date' in nodeRecord and nodeRecord['incorporation_date']:
        jsonData['Incorporated'] = nodeRecord['incorporation_date']
    if 'inactivation_date' in nodeRecord and nodeRecord['inactivation_date']:
        jsonData['Inactivated'] = nodeRecord['inactivation_date']
    if 'struck_off_date' in nodeRecord and nodeRecord['struck_off_date']:
        jsonData['Struck off'] = nodeRecord['struck_off_date']
    if 'note' in nodeRecord and nodeRecord['note']:
        jsonData['Notes'] = nodeRecord['note']

    #--entities and intermediaries used to have addresses, left here just in case they come back
    #--just store the list here, there may be related address nodes (usually duplicates of these!)
    addressList = []
    if 'address' in nodeRecord and nodeRecord['address']:  #--multiples separated by ; 
        addressList = nodeRecord['address'].split(';')
 
    #--split related nodes into addresses or disclosed relationships
    #--note the relationship records are one sided, must look for this entity on either side
    officerOfList = []
    edgeRecords = []
    edgeObj = conn.cursor()
    edgeSql = 'select * from %s_edges_view where node_1 = %s or node_2 = %s' % (nodeDatabase, nodeRecord['node_id'], nodeRecord['node_id'])
    edgeCursor = edgeObj.execute(edgeSql)        
    edgeHeader = [col[0] for col in edgeObj.description]
    edgeRow = edgeCursor.fetchone()
    while edgeRow:
        edgeRecord = dict(zip(edgeHeader, edgeRow))

        #--map the related node as an address
        if edgeRecord['node_1'] == nodeRecord['node_id'] and edgeRecord['rel_type'] == 'registered_address':
            if edgeRecord['node2_type'] == 'address': #--should always be true
                if edgeRecord['node2_desc'] not in addressList:
                    addressList.append(edgeRecord['node2_desc'])

        #--map the related node as a disclosed relationship
        else:
            edgeRecord['logical_node2'] = edgeRecord['node_2'] if edgeRecord['node_1'] == nodeRecord['node_id'] else edgeRecord['node_1']
            edgeRecord['logical_type2'] = edgeRecord['node2_type'] if edgeRecord['node_1'] == nodeRecord['node_id'] else edgeRecord['node1_type']
            edgeRecord['logical_desc2'] = edgeRecord['node2_desc'] if edgeRecord['node_1'] == nodeRecord['node_id'] else edgeRecord['node1_desc']
            edgeRecords.append(edgeRecord)

            #--also map the related node as a group name so can be used for matching
            if edgeRecord['node_1'] == nodeRecord['node_id'] and edgeRecord['rel_type'] == 'officer_of':
                if edgeRecord['node2_type'] == 'entity': #--should always be true
                    if edgeRecord['node2_desc'] not in officerOfList:
                        officerOfList.append(edgeRecord['node2_desc'])

        edgeRow = edgeCursor.fetchone()

    #--add the addresses by turning the plain list into a list of mapped addresses
    if addressList:
        subList = [] 
        for i in range(len(addressList)):
            if addressList[i] and type(addressList[i]) == str and len(addressList[i]) < 500 and addressList[i].upper().strip() not in ('NONE', 'NULL', '[NULL]'):
                subList.append({"ADDR_FULL": addressList[i]})
        if subList:
            if len(subList) == 1:
                jsonData.update(subList[0])
            else:
                jsonData['ADDRESS_LIST'] = subList
        
    #--create officer of attribute list
    if officerOfList and jsonData['ENTITY_TYPE'] == 'PERSON':
        subList = []
        for i in range(len(officerOfList)):
            if officerOfList[i] and type(officerOfList[i]) == str and len(officerOfList[i]) < 500 and officerOfList[i].upper().strip() not in ('NONE', 'NULL', '[NULL]'):
                subList.append({"GROUP_ASSOCIATION_ORG_NAME": officerOfList[i]})
        if subList:
            if len(subList) == 1:
                jsonData.update(subList[0])
            else:
                jsonData['OFFICER_OF_LIST'] = subList

	#--add the disclosed relationships, but summarize to eliminate duplication
    if edgeRecords:

        #--summarize (there are dupes!?)
        relationships = {}
        for edgeRecord in edgeRecords:
            if edgeRecord['logical_node2'] not in relationships:
                relationships[edgeRecord['logical_node2']] = {}
                relationships[edgeRecord['logical_node2']]['RELATED_REL_TYPE'] = edgeRecord['rel_type']
                relationships[edgeRecord['logical_node2']]['RELATED_RECORD_ID'] = edgeRecord['logical_node2']
                relationships[edgeRecord['logical_node2']]['RELATED_ENTITY_TYPE'] = edgeRecord['logical_type2']
                relationships[edgeRecord['logical_node2']]['RELATED_RECORD_NAME'] = edgeRecord['logical_desc2']
                relationships[edgeRecord['logical_node2']]['RELATED_FROM_DATE'] = baseLibrary.formatDate(edgeRecord['start_date']) if baseLibrary.formatDate(edgeRecord['start_date']) else ''
                relationships[edgeRecord['logical_node2']]['RELATED_THRU_DATE'] = baseLibrary.formatDate(edgeRecord['end_date']) if baseLibrary.formatDate(edgeRecord['end_date']) else ''
            else:
                if relationships[edgeRecord['logical_node2']]['RELATED_REL_TYPE'] not in edgeRecord['rel_type']:
                    relationships[edgeRecord['logical_node2']]['RELATED_REL_TYPE'] += '|' + edgeRecord['rel_type']
                nextFromDate = baseLibrary.formatDate(edgeRecord['start_date'])
                if nextFromDate and nextFromDate < relationships[edgeRecord['logical_node2']]['RELATED_FROM_DATE']: 
                    relationships[edgeRecord['logical_node2']]['RELATED_FROM_DATE'] = nextFromDate
                nextThruDate = baseLibrary.formatDate(edgeRecord['end_date'])
                if nextThruDate and nextThruDate < relationships[edgeRecord['logical_node2']]['RELATED_THRU_DATE']:
                    relationships[edgeRecord['logical_node2']]['RELATED_THRU_DATE'] = nextThruDate
            
        #--add to json
        relTypeCounts = {}
        subList = []
        for relatedKey in relationships:
            if noRelationships:
                if relationships[relatedKey]['RELATED_REL_TYPE'] not in relTypeCounts:
                    relTypeCounts[relationships[relatedKey]['RELATED_REL_TYPE']] = 0
                relTypeCounts[relationships[relatedKey]['RELATED_REL_TYPE']] += 1
                relAttr = relationships[relatedKey]['RELATED_REL_TYPE'].upper() + '_' + str(relTypeCounts[relationships[relatedKey]['RELATED_REL_TYPE']])
                jsonData[relAttr] = '%s (%s)' % (relationships[relatedKey]['RELATED_RECORD_ID'], relationships[relatedKey]['RELATED_RECORD_NAME'])
            else:
                relatedRecord = {}
                relatedRecord['RELATIONSHIP_TYPE'] = relationships[relatedKey]['RELATED_REL_TYPE']
                relatedRecord['RELATIONSHIP_KEY'] = '-'.join(sorted([str(relationships[relatedKey]['RELATED_RECORD_ID']), str(nodeRecord['node_id'])]))
                subList.append(relatedRecord)
        if subList:
            if len(subList) == 1:
                jsonData.update(subList[0])
            else:
                jsonData['RELATIONSHIP_LIST'] = subList

    #--add watch_list keys
    jsonData = baseLibrary.jsonUpdater(jsonData)

    #print(json.dumps(jsonData, indent=4, sort_keys=True))
    #pause()

    return jsonData

#----------------------------------------
if __name__ == '__main__':
    appPath = os.path.dirname(os.path.abspath(sys.argv[0]))

    global shutDown
    shutDown = False
    signal.signal(signal.SIGINT, signal_handler)
    procStartTime = time.time()
    progressInterval = 10000

    argparser = argparse.ArgumentParser()
    argparser.add_argument('-i', '--input_path', default=os.getenv('input_path'.upper(), None), type=str, help='path to the downloaded IJIC csv files.')
    argparser.add_argument('-o', '--output_file', default=os.getenv('output_file'.upper(), None), type=str, help='path and file name for the json output.')
    argparser.add_argument('-l', '--log_file', default=os.getenv('log_file'.upper(), None), type=str, help='optional statistics filename (json format).')
    argparser.add_argument('-d', '--database', default=os.getenv('database'.upper(), 'ALL'), type=str, help='choose: panama, bahamas, paradise, offshore or all (default=all)')
    argparser.add_argument('-t', '--node_type', default=os.getenv('node_type'.upper(), 'ALL'), type=str, help='choose: entity, intermediary, officer or all (default=all)')
    argparser.add_argument('-nr', '--no_relationships', default=False, action='store_true', help='do not create disclosed relationships')
    argparser.add_argument('-R', '--reload_csvs', default=False, action='store_true', help='reload from csvs, don\'t use cached data')
    args = argparser.parse_args()
    inputPath = args.input_path
    outputFileName = args.output_file
    logFile = args.log_file
    nodeDatabase = args.database.lower() if args.database else None
    nodeType = args.node_type.lower() if args.node_type else None
    noRelationships = args.no_relationships
    reloadFromCsvs = args.reload_csvs

    if not (inputPath):
        print('')
        print('Please supply the path to the downloaded IJIC csv files.')
        print('')

    if not (outputFileName):
        print('')
        print('Please supply an output file name.')
        print('')

    #--open output file
    try: outputFileHandle = open(outputFileName, "w", encoding='utf-8')
    except IOError as err:
        print('')
        print('Could not open output file %s for writing' % outputFileName)
        print(' %s' % err)
        print('')
        sys.exit(1)

    #--register the possible files
    inputFiles = []
    inputFiles.append({"fileName": "bahamas_leaks.nodes.address.csv", "nodeDatabase": "bahamas", "nodeType": "address"})
    inputFiles.append({"fileName": "bahamas_leaks.nodes.entity.csv", "nodeDatabase": "bahamas", "nodeType": "entity"})
    inputFiles.append({"fileName": "bahamas_leaks.nodes.intermediary.csv", "nodeDatabase": "bahamas", "nodeType": "intermediary"})
    inputFiles.append({"fileName": "bahamas_leaks.nodes.officer.csv", "nodeDatabase": "bahamas", "nodeType": "officer"})
    inputFiles.append({"fileName": "offshore_leaks.nodes.address.csv", "nodeDatabase": "offshore", "nodeType": "address"})
    inputFiles.append({"fileName": "offshore_leaks.nodes.entity.csv", "nodeDatabase": "offshore", "nodeType": "entity"})
    inputFiles.append({"fileName": "offshore_leaks.nodes.intermediary.csv", "nodeDatabase": "offshore", "nodeType": "intermediary"})
    inputFiles.append({"fileName": "offshore_leaks.nodes.officer.csv", "nodeDatabase": "offshore", "nodeType": "officer"})
    inputFiles.append({"fileName": "panama_papers.nodes.address.csv", "nodeDatabase": "panama", "nodeType": "address"})
    inputFiles.append({"fileName": "panama_papers.nodes.entity.csv", "nodeDatabase": "panama", "nodeType": "entity"})
    inputFiles.append({"fileName": "panama_papers.nodes.intermediary.csv", "nodeDatabase": "panama", "nodeType": "intermediary"})
    inputFiles.append({"fileName": "panama_papers.nodes.officer.csv", "nodeDatabase": "panama", "nodeType": "officer"})
    inputFiles.append({"fileName": "paradise_papers.nodes.address.csv", "nodeDatabase": "paradise", "nodeType": "address"})
    inputFiles.append({"fileName": "paradise_papers.nodes.entity.csv", "nodeDatabase": "paradise", "nodeType": "entity"})
    inputFiles.append({"fileName": "paradise_papers.nodes.intermediary.csv", "nodeDatabase": "paradise", "nodeType": "intermediary"})
    inputFiles.append({"fileName": "paradise_papers.nodes.officer.csv", "nodeDatabase": "paradise", "nodeType": "officer"})
    inputFiles.append({"fileName": "paradise_papers.nodes.other.csv", "nodeDatabase": "paradise", "nodeType": "other"})
    #--ensure edges files are last as views created on them require prior files
    inputFiles.append({"fileName": "bahamas_leaks.edges.csv", "nodeDatabase": "bahamas", "nodeType":"edges"})
    inputFiles.append({"fileName": "offshore_leaks.edges.csv", "nodeDatabase": "offshore", "nodeType": "edges"})
    inputFiles.append({"fileName": "panama_papers.edges.csv", "nodeDatabase": "panama", "nodeType": "edges"})
    inputFiles.append({"fileName": "paradise_papers.edges.csv", "nodeDatabase": "paradise", "nodeType": "edges"})
    #--create a table name for each file
    for i in range(len(inputFiles)):
        inputFiles[i]['tableName'] = inputFiles[i]['nodeDatabase'] + '_' + inputFiles[i]['nodeType']

    #--open database connection and load from csv if first time
    dbname = inputPath + (os.path.sep if inputPath[-1:] != os.path.sep else '') + 'ijic.db'
    dbExists = os.path.exists(dbname)
    if reloadFromCsvs and dbExists:  #--purge and reload
        print('')
        print('Cashed csv data purged!')
        os.remove(dbname)
    conn = sqlite3.connect(dbname)
    csv2db()

    #--initialize the statpack
    statPack = {}

    #--process each table
    for fileDict in inputFiles:
        if (fileDict['nodeDatabase'] == nodeDatabase.lower() or nodeDatabase.upper() == 'ALL') and (fileDict['nodeType'] == nodeType.lower() or nodeType.upper() == 'ALL'):
            processTable(fileDict)
            if shutDown:
                break

    outputFileHandle.close()

    #--write statistics file
    if logFile: 
        print('')
        statPack['BASE_LIBRARY'] = baseLibrary.statPack
        with open(logFile, 'w') as outfile:
            json.dump(statPack, outfile, indent=4, sort_keys = True)    
        print('Mapping stats written to %s' % logFile)

    print('')
    elapsedMins = round((time.time() - procStartTime) / 60, 1)
    if shutDown == 0:
        print('Process completed successfully in %s minutes!' % elapsedMins)
    else:
        print('Process aborted after %s minutes!' % elapsedMins)
    print('')
    
    sys.exit(0)
