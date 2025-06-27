# dependencies 
import pickle        # serialization library ->save/load  auth. credentials
import os
from datetime import datetime, timedelta
import time 
from google.auth.transport.requests import Request # HTTP transport for google auth
from google_auth_oauthlib.flow import InstalledAppFlow # Oauth 2.0  auth 
from googleapiclient.discovery import bulid #  api client builder 

# global configuration
# Permision levels: what are given aceess to 
# gmail.modify = can read, delete and modify emails
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

class GmailCleaner:
    def __init__(self):
        self.service = None

    def authenticate(self):
        """ Authenticate with Gmail API"""
        creds = None

        # load existing credentials
        # token.pichle is an object stored as bytes
        if os.path.exists("token.pickle"):
            with open("token.pickle", "rb") as token:
                # convert bytes into object
                creds = pickle.load(token) # deserialization
        
        # if no valid credentials or no credentials => get new one 
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                # token renewal; aka get fresh  token
                creds.refresh(Request()) 
            else: 
                # load credentials from file 
                # open web browser to Google login page
                # you log in  and approve permissions
                # google gives us fresh credentials
                # browser closes 
                flow = InstalledAppFlow.from_lient_secrets_file(
                    "../credentials.jason", SCOPES)
                creds = flow.run_local_server(port=0)

            # save credentials for next run
            # avoid having to log in next time 
            with open("tocken.pickle", "wb") as token:
                pickle.dump(creds, token) # convert object to bytes

        # create Gmail API client and set credentials
        self.service = build("gmail" , "v1", credentials=creds)
        print("Succesfully authentification with Gmail")

    def get_emails_by_query(self, query, max_results=500):
        """Get emails matching a sspecific query"""

        try:
            # gmial api call construction 
            results = self.service.users().messages.list(
                userId="me",
                q=query,                # gmail search syntax string 
                maxResults=max_results
            ).execute() # construct HTTP request 

            # response processing 
            emails = results.get("messages", []) # return empu list if no results
            return emails
        
        except Exception as e:
            print(f"Error fetching emials {e}")
            return []
    
    def delete_emails(self, message_ids, batch_size=100):
        """Delete emails in bathces"""

        # sanity check 
        if not message_ids:
            print("No emails to delete")
            return

        # counters
        total = len(message_ids)
        deleted = 0
        
        # process in batches  to avoid API limits 
        for i in range(0, total, batch_size):
            # get btach of email ids
            batch = message_ids[i:i + batch_size]

            try: 
                # iteratively delete email by email
                for msg_id in batch:
                    self.service.users().messages().delete(
                        userID="me",
                        id=msg_id
                    ).execute()
                    
                    deleted += 1
                
                print(f"Deleted {deleted/total} emails...")

                # delay program to respect API limits
                time.sleep(0.1)

            except Exception as e:
                print("Error deling batch: {e}")
                continue
    
        print(f"Succesfully deleted {deleted} emails")
    
    def clean_old_emails(self, days_old=90):
        """Delete emails older than the specified days"""

        date_cutoff = (datetime.now() - timedelta(days=days_old)).strftime("%Y/%m/%d")
        query = f"before:{date_cutoff}"

        print(f"Retrieving eimals older than {days_old} days...")
        messages = self.get_emails_by_query(query)

        # if messges found, extract id and delete
        if messages:
            msg_ids = [msg["id"] for msg in messages]
            print(f"Found {len(msg_ids)} old emails")
            self.delete_emails(msg_ids)
        else:
            print("No old emails found")
    
    def clean_by_sender(self, sender_email):
        """Clean all emails from a specific sender"""
        query = f"from:{sender_email}"

        print(f"Retrieving emails from sender {sender_email}...")
        messages = self.get_emails_by_query(query)

        # if messages found, extract the id and delete 
        if messages:
            msg_ids = [msg["id"] for msg in messages] 
            print(f"Found {len(msg_ids)} form sender {sender_email}")
            self.delete_emails(msg_ids)
        else:
            print("No emails found from sender")



