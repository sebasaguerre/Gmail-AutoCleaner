# dependencies 
import pickle        # serialization library ->save/load  auth. credentials
import os
import argparse
import schedule
import time 
from google.auth.transport.requests import Request # HTTP transport for google auth
from google_auth_oauthlib.flow import InstalledAppFlow # Oauth 2.0  auth 
from googleapiclient.discovery import bulid #  api client builder 
from datetime import datetime, timedelta

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
            results = self.service.users().messages().list(
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
    
    def delete_emails(self, message_ids, batch_size=500):
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
                self.service.users().messages().batchDelete(
                    userID="me",
                    id=batch
                ).execute()
                
                deleted += len(batch)
                time.sleep(0.1)
            
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
        """Delete all emails from a specific sender"""
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
    
    def clean_promotion_emails(self):
        """Delete all promotion/marketing emials"""
        queries = [
            "category:promotions",
            "unsubscribe",
            "subject:newsletter",
            "subject:sale",
            "subject:discount"
        ]

        all_msg_ids = []

        # loop over queries, get messages and extract ids 
        for query in queries:
            
            messages = self.get_emails_by_query(query)
            if messages:
                msg_ids = [msg["id"] for msg in messages]
                all_msg_ids.extend(msg_ids)

        # remove duplicate ids
        unique_ids = list(set(all_msg_ids))

        # delete all emails if not empty
        if unique_ids:
            print(f"Found {len(unique_ids)} promotion/marketing emails...")
            self.delete_emails(unique_ids)
        else:
            print("No promotion/marketing emials found")

    def clean_large_emails(self, size_mb):
        """Delete all emails above a certain size"""
        query = f"larger:{size_mb}M"

        print(f"Retriveing emails larger than {size_mb}MB...")
        messages = self.get_emails_by_query(query)

        if messages:
            msg_ids = [msg["id"] for msg in messages]
            print(f"Found {len(msg_ids)} large emails...")
            self.delete_emails(msg_ids)

        else:
            print("No large emails found")

    def clean_spam_emails(self):
        """Delete all emails flagged as spam by Gmail spam detector"""
        spam_messages = self.get_mails_by_query("in:spam")

        if spam_messages:
            msg_ids = [msg_ids["id"] for msg_ids in spam_messages]
            self.delete_emails(msg_ids)
        else:
            print("No spam email found")
    
    def empty_trash(self):
        """Empty the trash folder"""
        # get all messages form the trash 
        trash_messages = self.get_emails_by_query("in:trash")

        # extract messages and delete
        if trash_messages:
            msg_ids = [msg["id"] for msg in trash_messages]

            try:
                self.service.users().messages.batchDelete(
                    userId="me",
                    body={"ids": msg_ids}
                )
            except Exception as e:
                print(f"Error emptying trash: {e}")

def run_cleanup(args):
    """Run cleanup based on command line arguments"""

    cleaner = GmailCleaner()
    cleaner.authenticate()

    print("Starting Gmail cleanup...")

    if args.old_emails:
        cleaner.clean_old_emails(days_old=args.old_emails)
    
    if args.promotional:
        cleaner.clean_promotion_emails()
    
    if args.spam:
        cleaner.clean_spam_emails()
    
    if args.larger_emails():
        cleaner.clean_large_emails(size_mb=args.large_emails)
    
    if args.sender:
        for sender in args.sender:
            cleaner.clean_by_sender(sender)
    
    if args.empty_trash:
        cleaner.empty_trash()

    print("Cleanup finalzed!")

def run_schedualed_cleanup():
    """Run default cleanup for scheduled execution"""

    # Default cleanup 
    cleaner = GmailCleaner()
    cleaner.authenticate()

    # default cleanup
    cleaner.clean_promotion_emails()
    cleaner.clean_spam_emails()

    print("Schedualed cleanup completed!")

def main():

    pass

if __name__ == "__main__":
    main()