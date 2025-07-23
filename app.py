#!/usr/bin/env python

'''
Script Description: Allows you to write in and access messages from the file "Messages.json" 
Versions: 
Python 3.12.3
Flask 3.1.1
Werkzeug 3.1.3

'''
from flask import Flask
from flask import request
from flask import jsonify
from modules.modules import MessageStorage, WriteMessage, Initialization, ReadMessage, returnIfNotNull, DeleteMessage, CreateChannel, Except, is_isoformat, CreateUser, GetUsernames, GetUsernamesAndPasswords, ChangePassword, makeMD5, getPasswordSettings, checkPasswordComplexity, updateSettings, checkIfStringAndDigit, deactivateUser, checkIfUserValid, createToken, checkTokenValidity
import datetime
Initialization()

app = Flask(__name__)



# Store Messages
@app.route('/storemessage', methods=['POST'])
def storemessage():

    # If successful, receive the message data, get the message, create a return message, and write it into Messages.json
    try:
        messageData = request.get_json()
        actMessage = messageData.get("message")
        token = messageData.get("token")
        if not checkTokenValidity(token):
            return Except("The token is invalid.")
        if not actMessage or actMessage == "":
            Except("No message received!")

        WriteMessage(actMessage) # Writes message into Sqlite3 Database
        # Return the result of the operation
        return jsonify({ "result": "OK" }) 

    # if something went wrong, clear the return message, set "status" to ERROR, and return it into Messages.json
    except Exception as e:
        Except(e) 
    
# Allows you to view all of the messages
@app.route('/viewmessages', methods=["POST"])
def viewMessages():
    # number, user, channel, status, fromDate (datetime, ISO format), toDate
    # try:
        messageData = request.get_json()
        token = messageData.get("token")
        if not checkTokenValidity(token):
            return Except("The token is invalid.")
        dictionary = {}
        dictionary['number'] = None
        dictionary['user'] = None
        dictionary['channel'] = None
        dictionary['status'] = None
        dictionary['fromDate'] = None
        dictionary['toDate'] = None

        if messageData:
            if 'number' in messageData: dictionary['number'] = messageData.get("number")
            if 'user' in messageData: dictionary['user'] = messageData.get("user")
            if 'channel' in messageData: dictionary['channel'] = messageData.get("channel")
            if 'status' in messageData: dictionary['status'] = messageData.get("status")
            if 'fromDate' in messageData: dictionary['fromDate'] = messageData.get("fromDate")
            if 'toDate' in messageData: dictionary['toDate'] = messageData.get("toDate")
        if dictionary['number'] and not dictionary['number'].isdigit():
            return Except("That is not a number.")
        if dictionary['user'] and not dictionary['user'].isdigit():
            return Except("That is not a valid ID.")
        if dictionary['channel'] and not dictionary['channel'].isdigit():
            return Except("That is not a valid ID.")
        
        if dictionary["fromDate"] and not dictionary["toDate"]:
            dictionary["toDate"] = datetime.datetime.now().isoformat()
        elif dictionary["toDate"] and not dictionary["fromDate"]:
            dictionary['fromDate'] = datetime.datetime.min.isoformat()
        if dictionary['fromDate'] and not is_isoformat(dictionary['fromDate']):
            return Except("That is not a valid date format.")
        if  dictionary['toDate'] and not is_isoformat(dictionary['toDate']):
            return Except("That is not a valid date format.")

        dictCopy = dictionary.copy()
        for item in dictCopy:
            dictionary[item] = returnIfNotNull(dictionary[item])
            if not dictionary[item]:
                del dictionary[item]
        return jsonify(ReadMessage(**dictionary))
    # except Exception as e:
    #     return Except(e)
@app.route("/deletemessages", methods=["POST"])
def deleteMessages():
    try:
        messageData = request.get_json()
        id = messageData.get("id")
        token = messageData.get("token")
        if not checkTokenValidity(token):
            return Except("The token is invalid.")
        if id.isdigit():
            DeleteMessage(id)
        else:
            return Except("That is not an ID.")
        return jsonify({ "result": "OK" }) 

    except Exception as e:
        return Except(e) 

# Store Messages
@app.route('/createchannel', methods=['POST'])
def createchannel():

    # If successful, receive the message data, get the message, create a return message, and write it into Messages.json
    try:
        messageData = request.get_json()
        channelName = messageData.get("channel")
        token = messageData.get("token")
        if not checkTokenValidity(token):
            return Except("The token is invalid.")
        if not channelName:
            return Except("There is no channel name.")
        CreateChannel(channelName) # Writes message into Sqlite3 Database
        # Return the result of the operation
        return jsonify({ "result": "OK" }) 

    # if something went wrong, clear the return message, set "status" to ERROR, and return it into Messages.json
    except Exception as e:
        return Except(e)
    
@app.route('/register', methods=["POST"])
def register():
    # try:
        messageData = request.get_json()
        firstName = messageData.get("firstName")
        lastName = messageData.get("lastName")
        username = messageData.get("username")
        password = messageData.get("password")
        if not firstName or not lastName or not username or not password:
            return Except("Please fill in all fields.")
        if not firstName.isalpha() or not lastName.isalpha():
            return Except("All names have to include only letters.")
        if not username.isalnum():
            return Except("The username cannot contain special characters.")
        if username in GetUsernames():
            return Except("Username already exists, please select a different one!")
        if checkPasswordComplexity(password) == 'OKAY':
            CreateUser(f"{firstName}, {lastName}", username, makeMD5(password))
            return jsonify({ "result": "OK" }) 
        else:
            return checkPasswordComplexity(password)
    # except:
        # return Except("Something went wrong.")
@app.route("/authentication", methods=["POST"])
def authentication():
    # try:
        messageData = request.get_json()
        username = messageData.get("username")
        password = messageData.get("password")
        if not username or not password:
            return Except("Please enter all specified fields.")
        if not checkIfUserValid(username):
            return Except("That is an invalid username.")
        if not username.isalnum():
            return Except("The username cannot contain special characters.")
        if username in GetUsernames():
            for user in GetUsernamesAndPasswords():
                if user[0] == username and user[1] == makeMD5(password):
                    return jsonify({ "result": "Successfully authenticated!", "token": createToken(username) }) 
                elif user[0] == username and not user[1] == makeMD5(password):
                    return Except("The username and password do not match.")
        else:
            return Except("That is not an existing username.")
    # except:
        # return Except("Something went wrong.")

@app.route("/deleteuser", methods=["POST"])
def delete_user():
    messageData = request.get_json()
    username = messageData.get("username")
    password = messageData.get("password")
    token = messageData.get("token")
    if not checkTokenValidity(token):
        return Except("The token is invalid.")
    if not password or not username or not token:
        return Except("Please enter all necessary information.")
    if not checkIfUserValid(username):
        return Except("That is an invalid user.")

    match = False
    for user in GetUsernamesAndPasswords():
        if user[0] == username and user[1] == makeMD5(password):
            match = True
            deactivateUser(username)
            return jsonify({"result":"OK"})
    if not match:
        return Except("The password and username do not match.")


@app.route("/changepassword", methods=["POST"])
def changepassword():
    messageData = request.get_json()
    currentPassword = messageData.get("currentPassword")
    newPassword = messageData.get("newPassword")
    username = messageData.get("username")
    token = messageData.get("token")
    if not checkTokenValidity(token):
        return Except("The token is invalid.")
    if currentPassword == newPassword:
        return Except("That's the same password.")
    if not currentPassword or not newPassword or not username or not token:
        return Except("Please enter all necessary information.")
    if not checkIfUserValid(username):
        return Except("The username is invalid.")
    
    noMatch = False
    for user in GetUsernamesAndPasswords():
        if user[0] == username and user[1] == makeMD5(currentPassword):
            if not checkPasswordComplexity(newPassword) == 'OKAY':
                return checkPasswordComplexity(newPassword)  
            else:
                ChangePassword(makeMD5(newPassword), username)
                noMatch = True
                return jsonify({ "result": "OK" }) 
    if not noMatch:
        return Except("The password and username do not match.")

@app.route('/changesettings', methods=["POST"])
def changeSettings():
    messageData = request.get_json()
    passwordLength = messageData.get("passwordLength")
    specialSymbols = messageData.get("specialSymbols")
    capitalLetters = messageData.get("capitalLetters")
    number = messageData.get("number")
    includeSpaces = messageData.get("includeSpaces")
    token = messageData.get("token")
    if not checkTokenValidity(token):
        return Except("The token is invalid.")
    dictionary = {}
    dictionary["passwordLength"] = passwordLength
    dictionary["specialSymbols"] = specialSymbols
    dictionary["capitalLetters"] = capitalLetters
    dictionary["number"] = number
    dictionary["includeSpaces"] = includeSpaces
    dictCopy = dictionary.copy()
    for item in dictCopy:
        if not dictionary[item]:
            del dictionary[item]
            
    if not passwordLength and not specialSymbols and not capitalLetters and not number and not includeSpaces:
        return Except("All fields have been left blank.")
    if not checkIfStringAndDigit(passwordLength) or \
   not checkIfStringAndDigit(specialSymbols) or \
   not checkIfStringAndDigit(capitalLetters) or \
   not checkIfStringAndDigit(number) or \
   not checkIfStringAndDigit(includeSpaces):
        return Except("Make sure all values are of integer type.")
    else:
        if int(passwordLength) <= 2:
            return Except("The password length is too short.")
        if not (int(specialSymbols) == 0 or int(specialSymbols) == 1):
            return Except('The column "specialSymbols" can only be 1 or 0.')
        if not (int(capitalLetters) == 0 or int(capitalLetters) == 1):
            return Except('The column "capitalLetters" can only be 1 or 0.')
        if not (int(number) == 0 or int(number) == 1):
            return Except('The column "number" can only be 1 or 0.')
        if not (int(includeSpaces) == 0 or int(includeSpaces) == 1):
            return Except('The column "includeSpaces" can only be 1 or 0.')
        
        updateSettings(**dictionary)
        return jsonify({"result": "OK"})