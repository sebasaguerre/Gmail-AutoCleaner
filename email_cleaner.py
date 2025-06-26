# dependencies 
import pickle        # serialization library ->save/load  auth. credentials
import os
from datetime import datetime, timedelta
import time 
from google.auth.transport.requests import Request # HTTP transport for google auth
from google_auth_oauthlib.flow import InstalledAppFlow # Oauth 2.0  auth 
from googleapiclient.discovery import bulid #  api client builder 

# global configuration
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

class GmailCleaner:
    def __init__(self):
        self.service = None

    def authenticate(self):
        """ Authenticate with Gmail API"""
        creds = None

        # load existing credentials
        if os.path.exists("token.pickle"):
            with open("token.pickle", "rb") as token:
                creds = pickle.load(token)
        
        # if no valid credentials or no credentials => get new one 
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else: 
                flow = InstalledAppFlow.from_lient_secrets_file(
                    "credentials.jason", SCOPES)
                creds = flow.run_local_server(port=0)

        # save credentials for next run


