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
def WriteMessage(message, username, channel, status):
    conn = MessageStorage(dbName)
    cursor = conn.cursor()
    if (getChannelType(channel)) == "private":
        cursor.execute('''
            INSERT INTO PrivateMessages (message, user, channel, status)
            VALUES (?, ?, ?, ?)
    ''', (message, username, channel, status))
    else:
        cursor.execute('''
            INSERT INTO CommonMessages (message, user, channel, status)
            VALUES (?, ?, ?, ?)
    ''', (message, username, channel, status))
    conn.commit()
    conn.close()

def CanMessagesBeViewed(channel, username, password, channelPassword):
    if not channel or not username or not password:
        return Except("Please enter all necessary information.")
    if not checkIfUserValid(username):
        return Except("The username is invalid.")
    match = False
    for user in GetUsernamesAndPasswords():
        if user[0] == username and user[1] == makeMD5(password):
            match = True

    if not match:
        return Except("The username and password don't match.")
    if not getChannelID(channel):
        return Except("The channel is invalid.")
    if getChannelType(getChannelID(channel)) == "common":
        return "OKAY"
    elif getChannelType(getChannelID(channel)) == "private":
        print(getChannelOwners(channel))
        if not username in getChannelOwners(channel)[0]:
            return Except("You must be an owner of the chat to read from it.")
        else:
            return "OKAY"
    elif getChannelType(getChannelID(channel)) == "password_protected":
        if not channelPassword:
            return Except("Specify a password for password protected servers.")
        else:
            if not makeMD5(channelPassword) == getChannelPassword(channel):
                return Except("The password does not match the password protected server.")
            else:
                return "OKAY"


def CanMessageBeSent(username, password, message, other_user=None, channel=None, channelPassword=None):
    if not username or not password or not message:
        return Except("Please enter all necessary information.")
    if not other_user and not channel:
        return Except("Specify either a user or a channel.")
    if not checkIfUserValid(username):
        return Except("That is an invalid user.")
    if not getChannelID(channel):
        return Except("The channel is invalid.")    
    match = False
    for user in GetUsernamesAndPasswords():
        if user[0] == username and user[1] == makeMD5(password):
            match = True
    if not match:
        return Except("The username and password don't match.")
    if not other_user and channel:
        if not checkIfChannelExists(channel):
            return Except("The channel does not exist.")
        if getChannelType(getChannelID(channel)) == "private":
            if not username in getChannelOwners(channel):
                return Except("You must be an owner of the private chat to send messages.")
        elif getChannelType(getChannelID(channel)) == "password_protected":
            if not makeMD5(channelPassword) == getChannelPassword(channel):
                return Except("The password does not match the password protected server.")
            else:
                return getChannelID(channel)
        elif getChannelType(getChannelID(channel)) == "common":
            return getChannelID(channel)
    if other_user and not channel:
        if not checkIfUserValid(other_user):
            return Except("The other user is invalid.")
        if not doesDMexist(username, other_user):
            print("created channel")
            CreateChannel(f"{", ".join([username, other_user])}'s chat room", None, [username, other_user], "private", None)  
            channel = getChannelID(f"{", ".join([username, other_user])}'s chat room")    
        return getDMID(username, other_user)
        
def getDMID(user1, user2):
    conn = MessageStorage(dbName)
    cursor = conn.cursor()
    cursor.execute('SELECT id from Chats WHERE type="private" AND owners=?', (json.dumps([user1, user2]),))
    rows = cursor.fetchall()
    conn.close()
    return rows[0][0]
def doesDMexist(user1, user2):
    conn = MessageStorage(dbName)
    cursor = conn.cursor()
    cursor.execute('SELECT owners from Chats WHERE type="private"')
    rows = cursor.fetchall()
    conn.close()
    noMatch = True
    print(rows)
    if rows:
        for row in rows:
            if user1 in row[0] and user2 in row[0]:
                noMatch = False
    else:
        return False
    if noMatch:
        return False
    else:
        return True

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
    CREATE TABLE IF NOT EXISTS Chats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        creationDate TEXT DEFAULT CURRENT_TIMESTAMP,
        other_parameters TEXT,
        owners TEXT,
        type TEXT NOT NULL,
        status INTEGER NOT NULL,
        password TEXT
    )
''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Settings (
        parameterID INTEGER PRIMARY KEY AUTOINCREMENT,
        parameterName TEXT NOT NULL,
        parameterValue TEXT NOT NULL
    )
''')
    conn.commit()
    conn.close()

def checkIfValidChannel(channelName):
    conn = MessageStorage(dbName)
    cursor = conn.cursor()
    cursor.execute('SELECT id from Chats WHERE name=?', (channelName, ))
    rows = cursor.fetchall()
    conn.close()
    if rows:
        return True
    else:
        return False
def getChannelID(channelName):
    conn = MessageStorage(dbName)
    cursor = conn.cursor()
    cursor.execute("SELECT id from Chats WHERE name=?", (channelName, ))
    rows = cursor.fetchall()
    conn.close()
    if len(rows) > 0:
        return rows[0][0]
    else:
        return None
def getChannelType(channelID):
    conn = MessageStorage(dbName)
    cursor = conn.cursor()
    cursor.execute('SELECT type from Chats WHERE id=?', (channelID, ))
    rows = cursor.fetchall()
    print(rows)
    conn.close()
    return rows[0][0]   
def getChannelOwners(channelName):
    conn = MessageStorage(dbName)
    cursor = conn.cursor()
    cursor.execute('SELECT owners from Chats WHERE name=?', (channelName, ))
    rows = cursor.fetchall()
    conn.close()
    return rows[0]
def getChannelPassword(channelName):
    conn = MessageStorage(dbName)
    cursor = conn.cursor()
    cursor.execute('SELECT password from Chats WHERE name=?', (channelName, ))
    rows = cursor.fetchall()
    conn.close()
    return rows[0][0]
def getPasswordSettings():
    conn = MessageStorage(dbName)
    cursor = conn.cursor()
    cursor.execute("SELECT parameterID, parameterName, parameterValue FROM Settings")
    rows = cursor.fetchall()
    conn.close()
    return rows
def getTTL():
    conn = MessageStorage(dbName)
    cursor = conn.cursor()
    cursor.execute('SELECT parameterValue from Settings WHERE parameterName="TTL"')
    rows = cursor.fetchall()
    conn.close()
    return rows
def PasswordRestraint(reqName, currRequirement, reqList, password):
    if not reqName == "passwordLength" and not reqName == "includeSpaces":
        if checkIfStringAndDigit(currRequirement):
            if int(currRequirement) == 1:
                for char in password:
                    if char in reqList:
                        return True
            elif int(currRequirement) == 0:
                return True
    elif reqName == "passwordLength":
        if len(password) in reqList:
            return True
    elif reqName == "includeSpaces":
        if int(currRequirement) == 1:
            return True
        elif int(currRequirement) == 0:  
            if " " in password:
                return False  
            return True  
def checkPasswordComplexity(password):
    passwordSettings = getPasswordSettings()
    print(passwordSettings)
    rules_dict = {}
    for row in passwordSettings:
        if not row[1] == "TTL":
            rules_dict[row[1]] = row[2]
    req_array = {"passwordLength":list(range(int(rules_dict["passwordLength"]), 100)), 
                 "specialSymbols":string.punctuation,
                 "capitalLetters":string.ascii_uppercase,
                 "number":string.digits,
                 "includeSpaces":" "}

    for setting in passwordSettings:
        if not setting[1] == "TTL" and not PasswordRestraint(setting[1], setting[2], req_array[setting[1]], password):
            return Except(f"The '{setting[1]}' is invalid.")
    return "OKAY"
    
def CreateUser(name, username, password):
    conn = MessageStorage(dbName)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO Users (name, username, password, status)
        VALUES (?, ?, ?, 1)
 ''', (name, username, password))
    conn.commit()
    conn.close()
def CreateChannel(channelName, other_parameters, owners, type, password=None):
    conn = MessageStorage(dbName)
    cursor = conn.cursor()
    if not password and not other_parameters:
        cursor.execute('''
            INSERT INTO Chats (name, owners, type, status)
            VALUES (?, ?, ?, 1)
    ''', (channelName, json.dumps(owners), type))
    elif not password and other_parameters:
        cursor.execute('''
            INSERT INTO Chats (name, owners, type, status, other_parameters)
            VALUES (?, ?, ?, 1, ?)
    ''', (channelName, json.dumps(owners), type, other_parameters))        
    elif password and other_parameters:
        cursor.execute('''
            INSERT INTO Chats (name, owners, type, status, other_parameters, password)
            VALUES (?, ?, ?, 1, ?, ?)
    ''', (channelName, json.dumps(owners), type, other_parameters, password))  
    elif password and not other_parameters:
        cursor.execute('''
            INSERT INTO Chats (name, owners, type, status, password)
            VALUES (?, ?, ?, 1, ?)
    ''', (channelName, json.dumps(owners), type, password))  
    conn.commit()
    conn.close()
def getUserID(username):
    conn = MessageStorage(dbName)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id
        FROM Users
        WHERE username = ?
    ''', (username, ))    
    rows = cursor.fetchall()
    conn.close()
    return rows
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
    tableName = "CommonMessages"
    channel = getChannelID(channel)
    if getChannelType(channel) == "private":
        tableName = "PrivateMessages"
    if not user and not fromDate and not toDate:
        cursor.execute(f'''
            SELECT *
            FROM {tableName}
            WHERE channel = ? AND status = ?
            ORDER BY id DESC
            LIMIT ?
        ''', (channel, status, number))    
    elif user and not fromDate and not toDate:
        cursor.execute(f'''
            SELECT *
            FROM {tableName}
            WHERE channel = ? AND status = ? AND user = ?
            ORDER BY id DESC
            LIMIT ?
        ''', (channel, status, user, number)) 
    elif not user and fromDate and toDate:
        cursor.execute(f'''
            SELECT *
            FROM {tableName}
            WHERE channel = ? AND status = ? AND time BETWEEN ? and ?
            ORDER BY id DESC
            LIMIT ?
        ''', (channel, status, fromDate, toDate, number))  
    elif user and fromDate and toDate:
        cursor.execute(f'''
            SELECT *
            FROM {tableName}
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

def updateSettings(**args):
    conn = MessageStorage(dbName)
    cursor = conn.cursor()
    arguments = {}
    for i in args:
        addToListIfNumber(arguments, args[i], i)

    if arguments:
        settingsColumns = list(arguments.keys())
        settingsRow = list(arguments.values())
        for i in range(len(settingsColumns)):
            cursor.execute("SELECT COUNT(*) FROM Settings WHERE parameterName = ?", (settingsColumns[i],))
            if not cursor.fetchone()[0]:
                print(settingsColumns[i], settingsRow[i])
                cursor.execute(f"INSERT INTO settings (parameterName, parameterValue) VALUES (?, ?)", (settingsColumns[i], settingsRow[i]))

            else:
                cursor.execute("UPDATE settings SET parameterValue = ? WHERE parameterName = ?", (settingsRow[i], settingsColumns[i]))
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
    token["TTL"] = time.time()+(int(getTTL()[0][0])*60*60)
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
def checkIfChannelExists(channelName):
    conn = MessageStorage(dbName)
    cursor = conn.cursor()
    cursor.execute("SELECT name, status FROM Chats")
    rows = cursor.fetchall()
    conn.close()
    channel_exists = False
    for row in rows:
        if row[0] == channelName:
            channel_exists = True
            if str(row[1]) == "1":
                return True
            else:
                return False
    if not channel_exists:
        return False
