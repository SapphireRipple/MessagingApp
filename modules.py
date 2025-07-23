import json
import os
import sqlite3
from flask import jsonify
import datetime
import dateutil
import hashlib
import string
import base64
import time
dbName = "Messages.db"



#  ------                MESSAGES:                ------
# Makes a connection to the database
def MessageStorage(filename):
    conn = sqlite3.connect(filename)
    conn.commit()
    return conn

# Deletes a message
def DeleteMessage(id):
    conn = MessageStorage(dbName)
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM CommonMessages WHERE id = ?;
 ''', (id, ))
    conn.commit()
    conn.close()

# Writes a message
def WriteMessage(message):
    conn = MessageStorage(dbName)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO CommonMessages (message, user, channel, status)
        VALUES (?, 1, 1, 1)
 ''', (message, ))
    conn.commit()
    conn.close()


def Initialization():
    conn = MessageStorage(dbName)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS CommonMessages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        message TEXT NOT NULL,
        time TEXT DEFAULT CURRENT_TIMESTAMP,
        user INTEGER NOT NULL,
        channel INTEGER NOT NULL,
        status INTEGER NOT NULL
    )
 ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS PrivateMessages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        message TEXT NOT NULL,
        time TEXT DEFAULT CURRENT_TIMESTAMP,
        user INTEGER NOT NULL,
        channel INTEGER NOT NULL,
        status INTEGER NOT NULL
    )
 ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        username TEXT NOT NULL,
        password TEXT NOT NULL,
        status INTEGER NOT NULL
    )
 ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Channels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
    )
''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Settings (
        passwordLength INTEGER NOT NULL,
        specialSymbols INTEGER NOT NULL,
        capitalLetters INTEGER NOT NULL,
        number INTEGER NOT NULL,
        includeSpaces INTEGER NOT NULL
    )
''')
    conn.commit()
    conn.close()

def getPasswordSettings():
    conn = MessageStorage(dbName)
    cursor = conn.cursor()
    cursor.execute("SELECT passwordLength, specialSymbols, capitalLetters, number, includeSpaces FROM Settings")
    rows = cursor.fetchall()
    conn.close()
    return rows

def PasswordRestraint(prevRequirement, currRequirement, reqList, password):
    if prevRequirement:
        if checkIfStringAndDigit(currRequirement):
            if int(currRequirement) == 1:
                for char in password:
                    if char in reqList:
                        return True
            elif int(currRequirement) == 0:
                return True
        else:
            return False
def checkPasswordComplexity(password):
    passwordSettings = getPasswordSettings()[0]
    passwordLength = passwordSettings[0]
    specialSymbols = passwordSettings[1]
    capitalLetters = passwordSettings[2]
    number = passwordSettings[3]
    includeSpaces = passwordSettings[4]
    if passwordLength == None or specialSymbols == None or capitalLetters == None or number == None or includeSpaces == None:
        return Except("Not all settings exist.")
    correctLength = False
    if checkIfStringAndDigit(passwordLength):
        if len(password) >= int(passwordLength):
            correctLength = True
        else:
            return Except("The password is too short.")
    else:
        return Except("The 'passwordLength' settings are invalid.")
    
    
    containsSpecialSymbol = False
    if not PasswordRestraint(correctLength, specialSymbols, string.punctuation, password):
        return Except("The password contains no special symbols.")
    else:
        containsSpecialSymbol = True

    containsOneUppercase = False
    if not PasswordRestraint(containsSpecialSymbol, capitalLetters, string.ascii_uppercase, password):
        return Except("The password contains no uppercase characters.")
    else:
        containsOneUppercase = True

    containsANumber = False
    if not PasswordRestraint(containsOneUppercase, number, string.digits, password):
        return Except("The password contains no numbers.")
    else:
        containsANumber = True

    notContainsASpace = False
    if PasswordRestraint(containsANumber, includeSpaces, " ", password):
        return Except("The password contains spaces.")
    else:
        notContainsASpace = True

    if notContainsASpace and correctLength and containsANumber and containsOneUppercase and containsSpecialSymbol:
        return 'OKAY'
    else:
        return Except("The password contains spaces.")

def CreateUser(name, username, password):
    conn = MessageStorage(dbName)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO Users (name, username, password, status)
        VALUES (?, ?, ?, 1)
 ''', (name, username, password ))
    conn.commit()
    conn.close()
def CreateChannel(channelName):
    conn = MessageStorage(dbName)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO Channels (name)
        VALUES (?)
 ''', (channelName, ))
    conn.commit()
    conn.close()

def GetUsernames():
    conn = MessageStorage(dbName)
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM Users")
    rows = cursor.fetchall()
    usernames = [row[0] for row in rows]
    conn.close()
    return usernames

def GetUsernamesAndPasswords():
    conn = MessageStorage(dbName)
    cursor = conn.cursor()
    cursor.execute("SELECT username, password FROM Users")
    rows = cursor.fetchall()
    conn.close()
    return rows
def ChangePassword(newPassword, username):
    conn = MessageStorage(dbName)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE Users
        SET password = ?
        WHERE username = ?
    """, (newPassword, username))   
    conn.commit() 
    conn.close()
def deactivateUser(username):
    conn = MessageStorage(dbName)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE Users
        SET status = ?
        WHERE username = ?
    """, (0, username))   
    conn.commit() 
    conn.close()
def ReadMessage(number=20, user=None, channel=1, status=1, fromDate=None, toDate=None):
    conn = MessageStorage(dbName)
    cursor = conn.cursor()
    if not user and not fromDate and not toDate:
        cursor.execute('''
            SELECT *
            FROM CommonMessages
            WHERE channel = ? AND status = ?
            ORDER BY id DESC
            LIMIT ?
        ''', (channel, status, number))    
    elif user and not fromDate and not toDate:
        cursor.execute('''
            SELECT *
            FROM CommonMessages
            WHERE channel = ? AND status = ? AND user = ?
            ORDER BY id DESC
            LIMIT ?
        ''', (channel, status, user, number)) 
    elif not user and fromDate and toDate:
        cursor.execute('''
            SELECT *
            FROM CommonMessages
            WHERE channel = ? AND status = ? AND time BETWEEN ? and ?
            ORDER BY id DESC
            LIMIT ?
        ''', (channel, status, fromDate, toDate, number))  
    elif user and fromDate and toDate:
        cursor.execute('''
            SELECT *
            FROM CommonMessages
            WHERE channel = ? AND status = ? AND time BETWEEN ? and ? AND user = ?
            ORDER BY id DESC
            LIMIT ?
        ''', (channel, status, fromDate, toDate, user, number))  
    # Converts return data into a dictionary
    rows = cursor.fetchall()
    columns = []
    for i in cursor.description:
        columns.append(i[0])
    json_return = {}
    y = 0
    for row in rows:
        y += 1
        x = 0
        for col in columns:
            if not y in json_return:
                json_return[y] = {}
            json_return[y][col] = row[x]
            x += 1
    conn.commit()
    conn.close()
    return json_return

def returnIfNotNull(number):
    if number != None:
        if number.isdigit():
            return int(number)
        else:
            return number
    else:
        return None
def Except(exception):
    return jsonify({ "result": f"ERROR: {exception}" })

def is_isoformat(s):
    try:
        dateutil.parser.isoparse(s)
        return True
    except ValueError:
        return False
    
def makeMD5(password):
    return hashlib.md5(password.encode('utf-8')).hexdigest()

def updateSettings(passwordLength=False, specialSymbols=False, capitalLetters=False, number=False, includeSpaces=False):
    conn = MessageStorage(dbName)
    cursor = conn.cursor()

    arguments = {}
    addToListIfNumber(arguments, passwordLength, "passwordLength")
    addToListIfNumber(arguments, specialSymbols, "specialSymbols")
    addToListIfNumber(arguments, capitalLetters, "capitalLetters")
    addToListIfNumber(arguments, number, "number")
    addToListIfNumber(arguments, includeSpaces, "includeSpaces")
    if arguments:
        settingsColumns = list(arguments.keys())
        settingsRow = tuple(arguments.values())
        cursor.execute("SELECT COUNT(*) FROM Settings")
        if cursor.fetchone()[0] == 0:
            cursor.execute(f"INSERT INTO settings ({', '.join(settingsColumns)}) VALUES ({("?, "*len(settingsRow))[:-2]})", settingsRow)
        else:
            cursor.execute( f"UPDATE settings SET {", ".join([f"{col} = ?" for col in settingsColumns])}", settingsRow)
    conn.commit()
    conn.close()
def addToListIfNumber(dict_, argument, key):
    if checkIfStringAndDigit(argument):
        dict_[key] = argument
def checkIfStringAndDigit(item):
    if isinstance(item, str):
        if item.isdigit():
            return True
        else:
            return False
    elif isinstance(item, int):
        return True
    else:
        return False
    
def createToken(username):
    token = {}
    token["username"] = username
    token["timestamp"] = time.time()
    token["TTL"] = time.time()+86400
    encoded_token = encodeBase64(json.dumps(token))
    return encoded_token
def encodeBase64(json_data):
    json_bytes = json_data.encode('utf-8')
    base64json = base64.b64encode(json_bytes)
    token = base64json.decode('utf-8')
    return token
def checkTokenValidity(token):
    try:
        if token:
            decoded_token = base64.b64decode(token).decode('utf-8')
            token_json = json.loads(decoded_token)
            min_time = token_json["timestamp"]
            max_time = token_json["TTL"]
            username = token_json["username"]
            if checkIfUserValid(username):
                if min_time < time.time() < max_time:
                    return True
                else:
                    return False
            else:
                return False
    except:
        return False
def checkIfUserValid(username):
    conn = MessageStorage(dbName)
    cursor = conn.cursor()
    cursor.execute("SELECT username, status FROM Users")
    rows = cursor.fetchall()
    conn.close()
    username_exists = False
    for row in rows:
        if row[0] == username:
            username_exists = True
            if str(row[1]) == "1":
                return True
            else:
                return False
    if not username_exists:
        return False
