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
from modules import MessageStorage, WriteMessage, Initialization, ReadMessage, returnIfNotNull, DeleteMessage, CreateChannel, Except, is_isoformat, CreateUser, GetUsernames, GetUsernamesAndPasswords, ChangePassword, makeMD5, getPasswordSettings, checkPasswordComplexity, updateSettings, checkIfStringAndDigit, deactivateUser, checkIfUserValid, createToken, checkTokenValidity, getUserID, checkIfChannelExists, getChannelID, getChannelType, checkIfValidChannel, CanMessageBeSent, CanMessagesBeViewed
import datetime
import json
Initialization()

app = Flask(__name__)



# Store Messages
@app.route('/storemessage', methods=['POST'])
def storemessage():

    # If successful, receive the message data, get the message, create a return message, and write it into Messages.json
    # try:
        messageData = request.get_json()
        actMessage = messageData.get("message")
        token = messageData.get("token")
        username = messageData.get("username")
        password = messageData.get("password")
        otherUsername = messageData.get("receiverUsername")
        channel = messageData.get("channel")
        channelPassword = messageData.get("channelPassword")
        if not checkTokenValidity(token):
            return Except("The token is invalid.")
       
        result = CanMessageBeSent(username, password, actMessage, otherUsername, channel, channelPassword)
        if isinstance(result, int):
            WriteMessage(actMessage, username, result, 1)
        else:
            return result

 # Writes message into Sqlite3 Database
        # Return the result of the operation
        return jsonify({ "result": "OK" }) 

    # if something went wrong, clear the return message, set "status" to ERROR, and return it into Messages.json
    # except Exception as e:
    #     return Except(e) 
    
# Allows you to view all of the messages
@app.route('/viewmessages', methods=["POST"])
def viewMessages():
    # number, user, channel, status, fromDate (datetime, ISO format), toDate
    # try:
        messageData = request.get_json()
        token = messageData.get("token")
        username = messageData.get("username")
        password = messageData.get("password")
        channel = messageData.get("channel")
        channelPassword = messageData.get("channelPassword")
        if not checkTokenValidity(token):
            return Except("The token is invalid.")
        result = CanMessagesBeViewed(channel, username, password, channelPassword)
        if not result == "OKAY":
            return result
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
    # try:
        messageData = request.get_json()
        channelName = messageData.get("channel")
        owners = messageData.get("owners")
        type = messageData.get("type")
        token = messageData.get("token")
        password = messageData.get("password")
        other_parameters = messageData.get("other_parameters")
        if (checkIfValidChannel(channelName)):
            return Except("A channel with that name already exists.")

        if not (type == "common" or type == "private" or type == "password_protected"):
            return Except("The type is invalid.")
        if not checkTokenValidity(token):
            return Except("The token is invalid.")
        if not owners or not type:
            return Except("Fill out all required fields.")
        print(channelName)
        if (not channelName and len(owners) < 2) or not (not channelName and type == "private" and len(owners) == 2) and not channelName:
            return Except("There is no channel name.")
        elif not channelName and len(owners) == 2 and type == "private":
            channelName = f"{", ".join(owners)}'s chat room"
        elif not type == "private" and len(owners) > 2:
            return Except("A private channel can only have two people.")
        elif channelName and (type == "common" or type == "password_protected"):
            if (not channelName.isalnum()):
                return Except("The channel name is invalid.")
                              
        for owner in owners:
            if not checkIfUserValid(owner):
                return Except(f"{owner} is an invalid user!")
        if type == "password_protected" and not password:
            return Except("Password protected channels require a password.")
        ownerIDs = []
        for user in owners:
            ownerIDs.append(getUserID(user)[0][0])
        if not checkIfChannelExists(channelName):
            if password and checkPasswordComplexity(password) == "OKAY":
                print("passowrdOK")
                password = makeMD5(password)
                print(password)
            elif password and not checkPasswordComplexity(password) == "OKAY":
                return checkPasswordComplexity(password)
            CreateChannel(channelName, other_parameters, ownerIDs, type, password) # Writes message into Sqlite3 Database
        else:
            return Except("A channel with that name already exists.")
        # Return the result of the operation
        return jsonify({ "result": "OK" }) 

    # if something went wrong, clear the return message, set "status" to ERROR, and return it into Messages.json
    # except Exception as e:
    #     return Except(e)
    
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
    # except Exception as e:
    #     return Except(e) 
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
    # except Exception as e:
    #     return Except(e) 

@app.route("/deleteuser", methods=["POST"])
def delete_user():
    try:
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
    except Exception as e:
        return Except(e) 

@app.route("/changepassword", methods=["POST"])
def changepassword():
    # try:
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
    # except Exception as e:
    #     return Except(e) 
@app.route('/changesettings', methods=["POST"])
def changeSettings():
    # try:
        messageData = request.get_json()
        token = messageData.get("token")
        if not checkTokenValidity(token):
            return Except("The token is invalid.")
        dictionary = messageData.copy()
        del dictionary["token"]
        containsValue = False
        for item in dictionary:
            if not dictionary[item] == "":
                containsValue = True
                if not checkIfStringAndDigit(dictionary[item]):
                    return Except("Make sure all values are of integer type.")
                elif item == "passwordLength" and int(dictionary[item]) <= 2:
                    return Except("The password length is too short.")
                elif not item == "TTL" or not item == "passwordLength" and not int(dictionary[item]) == 1 and not int(dictionary[item]) == 0:
                    return Except(f'The column "{item}" can only be 1 or 0.')
                elif item == "TTL" or item == "passwordLength":
                    return Except(f"The {item} is invalid.")
        
        if not containsValue:
            return Except("All fields have been left blank.")
        
        updateSettings(**dictionary)
        return jsonify({"result": "OK"})
    # except Exception as e:
    #     return Except(e) 