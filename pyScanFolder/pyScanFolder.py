'''
Created on 11.07.2013

@author: rb
'''

import getopt
import sys
import os
import MySQLdb
import ConfigParser
import hashlib
import pyexiv2


ConfigFile='RBPicsDB.cfg'

DbHost = ''
DbDatabase = ''
DbUser = ''
DbPassword = ''


verbindung = None
def main():
    argv = sys.argv
    ScanDir = './'
    NewTables = False
    
    try:
        opts, _ = getopt.getopt(argv[1:], 'hf:nd:', ['help', 'file=', 'new', 'directory='])
    except getopt.GetoptError:
        sys.exit(1)
    
    for opt, arg in opts :
        if opt in ('-h', '--help'):
            printHelp()
        
        if opt in ('-f', '--file'):
            ConfigFile = str(arg)    

        if opt in ('-n', '--new'):
            NewTables = True
            
        if opt in ('-d', '--directory'):
            ScanDir = str(arg)
    
    AbsScanDir = os.path.abspath(ScanDir)
    
    (DbHost, DbDatabase, DbUser, DbPassword) = ReadDatabaseSettings()
    try:
        global verbindung 
        verbindung = MySQLdb.connect(DbHost,
                                     DbUser,
                                     DbPassword,
                                     DbDatabase)
    except MySQLdb.DatabaseError:
        sys.exit(1)

    if NewTables == True:
        newTables()
    
    addPath2Db(AbsScanDir)
    addBilder2Db(AbsScanDir, NewTables)
    sys.exit(0)
    
def addBilder2Db(Pfad, EmptyDatabase = False):
    daten = []
    cursor = verbindung.cursor()
    SQL = "SELECT ID FROM Verzeichnisse WHERE Pfad = '%s'" %Pfad
    cursor.execute(SQL)
    Antwort = cursor.fetchone()
    PfadId = int(Antwort[0])
    Dateien = os.listdir((Pfad+"/"))
    Dateien.sort()
    for Datei in Dateien:
        if Datei.endswith(".jpg"):
            if EmptyDatabase == False:
                SQL="SELECT Count(*) FROM Bilder WHERE Name = '%s' AND Pfad = '%s' "%(Datei, PfadId)
                cursor.execute(SQL)
                Antwort = cursor.fetchone()
            else:
                Antwort = 0
                
            if Antwort == 0:
                Md5 = md5ForFile('%s/%s'%(Pfad,Datei))
                exif = pyexiv2.ImageMetadata('%s/%s'%(Pfad,Datei))
                try :
                    exif.read()
                    (Width, Height) = exif.dimensions
                except:
                    Width = 0
                    Height = 0
                
                datum = (Datei, PfadId, Width, Height, Md5)
                daten.append(datum)
                if len(daten) == 1000:
                    addBild2Db(daten)
                    daten = []
    
    if daten != None:        
        addBild2Db(daten)

def addBild2Db(Daten):
    cursor = verbindung.cursor()
    SQL="INSERT INTO Bilder(Name, Pfad, Width, Height, Md5Sum) VALUES(%s, %s, %s, %s, %s)"
    cursor.executemany(SQL, Daten)
    verbindung.commit()

def addPath2Db(Pfad):
    cursor = verbindung.cursor()
    SELECT = "SELECT * FROM Verzeichnisse WHERE Pfad = '%s'" %Pfad
    cursor.execute(SELECT)
    Antwort = cursor.fetchone()
    if Antwort == None:
        INSERT = "INSERT INTO Verzeichnisse(Pfad) VALUES('%s')" %Pfad
        cursor.execute(INSERT)
        verbindung.commit()
        SELECT = "SELECT * FROM Verzeichnisse WHERE Pfad = '%s'" %Pfad
        cursor.execute(SELECT)
        Antwort = cursor.fetchone()
        
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
    
def newTables():
    cursor = verbindung.cursor()
    #Drop Table Bilder
    SQL="DROP TABLE IF EXISTS Bilder"
    cursor.execute(SQL)
    #Drop Table Verzeichnisse
    SQL="DROP TABLE IF EXISTS Verzeichnisse"
    cursor.execute(SQL)
    #Create Table Verzeichnisse
    SQL="CREATE TABLE Verzeichnisse( \
        ID INT PRIMARY KEY AUTO_INCREMENT,\
        Pfad VARCHAR(255))"
    cursor.execute(SQL)
    #Create Table Bilder
    SQL="CREATE TABLE Bilder(\
        ID INT PRIMARY KEY AUTO_INCREMENT,\
        Name VARCHAR(255),\
        Pfad INT,\
        Width INT,\
        Height INT,\
        Depth INT,\
        MD5Sum VARCHAR(32) UNIQUE,\
        ViewCntr INT NOT NULL DEFAULT 0,\
        LastViewed DATE)"
    cursor.execute(SQL)

def newTableVerzeichnisse():
    pass

def newTableBild():
    pass


def printHelp():
    pass
    
def md5ForFile(path, block_size=256*128):
    '''
    Block size directly depends on the block size of your filesystem
    to avoid performances issues
    Here I have blocks of 4096 octets (Default NTFS)
    '''
    md5 = hashlib.md5()
    with open(path,'rb') as f: 
        for chunk in iter(lambda: f.read(block_size), b''): 
            md5.update(chunk)
    return md5.hexdigest() 


if __name__ == '__main__':
    main()
