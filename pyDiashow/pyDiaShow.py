'''
Created on 11.07.2013

@author: rb
'''

import getopt
import sys
import os
import MySQLdb
import ConfigParser
import time
import pyexiv2


ConfigFile='RBPicsDB.cfg'

DbHost = ''
DbDatabase = ''
DbUser = ''
DbPassword = ''


verbindung = None
def main():
    argv = sys.argv
    ListDirs = False;
    PicDirectory = './'
    SleepTime = 60
    LinkName = 'Bild.jpg' 
    try:
        opts, _ = getopt.getopt(argv[1:], 'hf:d:t:l:', ['help', 'file=', 'directory=', 'listdirs', 'time=', 'linkto='])
    except getopt.GetoptError:
        sys.exit(1)
    
    for opt, arg in opts :
        if opt in ('-h', '--help'):
            printHelp()
        
        if opt in ('-f', '--file'):
            ConfigFile = str(arg)    

        if opt in ('-d', '--directory'):
            PicDirectory = str(arg)
            pass
        
        if opt in ('--listdirs'):
            ListDirs = True
    
        if opt in ('-t', '--time'):
            SleepTime = float(arg)
        
        if opt in ('-l', '--linkto'):
            LinkName = str(arg)
                
    (DbHost, DbDatabase, DbUser, DbPassword) = ReadDatabaseSettings()
    try:
        global verbindung 
        verbindung = MySQLdb.connect(DbHost,
                                     DbUser,
                                     DbPassword,
                                     DbDatabase)
    except MySQLdb.DatabaseError:
        sys.exit(1)


    if ListDirs == True:
        Antwort = listDirs()
        for Id, Verzeichnis in Antwort:
            print "Verzeichnis: %s; ID: %d" %(Verzeichnis, Id)
        sys.exit(0)

    PicDirectory= os.path.abspath(PicDirectory)
                
    Antwort = getDirs("ID, Pfad", "WHERE Pfad='%s'" %PicDirectory)
    Id, Verzeichnis = Antwort[0] 

    while(1):
        (BildId, Bildname) = getBildFromDb(Id)
        try:
            os.remove(LinkName)
        except:
            pass
        try:
            os.symlink("%s/%s"%(Verzeichnis, Bildname), LinkName)
        except:
            print "Symlink konnte nicht erstellt werden!"
        print "%s/%s hat die ID: %s" %(Verzeichnis, Bildname, BildId)
        updateBildinfo(BildId)
        
        time.sleep(SleepTime)
    sys.exit(0)

def updateBildinfo(BildId):
    cursor = verbindung.cursor()
    SQL = "UPDATE Bilder SET ViewCntr = ViewCntr + 1 WHERE ID = %s" %BildId
    cursor.execute(SQL)
    verbindung.commit()

def getDirs(what="*", where=""):
    cursor = verbindung.cursor()
    SQL = "SELECT %s FROM Verzeichnisse %s"%(what,where)
    cursor.execute(SQL)
    Antwort = cursor.fetchall()
    return Antwort
    
def listDirs():
    return getDirs()

def getBildFromDb(PfadId):
    cursor = verbindung.cursor()
    SQL = "SELECT Id, Name FROM Bilder WHERE Pfad = '%s' AND ViewCntr = (SELECT min(ViewCntr) FROM Bilder) ORDER by RAND() LIMIT 1" %PfadId
    cursor.execute(SQL)
    Antwort = cursor.fetchone()
    return Antwort
        
def ReadDatabaseSettings():
    DbHost = ''
    DbDatabase = ''
    DbUser = ''
    DbPassword = ''
    
    config = ConfigParser.ConfigParser()
    try:
        config.read(ConfigFile)
    except ConfigParser.Error:
        sys.exit(1)
    
    items = config.items('Database')
    for Schluessel, Wert in items:
        if Schluessel in 'host':
            DbHost = Wert
        if Schluessel in 'database':
            DbDatabase = Wert
        if Schluessel in 'user':
            DbUser = Wert
        if Schluessel in 'password':
            DbPassword = Wert
        
    return(DbHost, DbDatabase, DbUser, DbPassword)
    
def printHelp():
    pass
    
if __name__ == '__main__':
    main()
