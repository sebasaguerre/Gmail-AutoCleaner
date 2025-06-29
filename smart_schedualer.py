import json 
import os
from datetime import datetime, timedelta
from email_cleaner import GmailCleaner

class SmartScheduler:
    def __int__(self, state_file="gmail_cleaner_state.jason"):
        self.state_file = state_file
        self.load_state()

    def load_state(self):
        """Load last execution of program from file"""
        # if file exist load, else create empty dictionary
        if os.path.exists(self.state_file):
            with open(self.state_file, "r") as f:
                self.state = json.load(f)
        else:
            self.state = {}

    def save_state(self):
        """Save execution time to file"""
        # overwritte file with current execution time 
        with open(self.state_file , "w") as f:
            json.dump(self.state, f ,indent=2)
    
    def should_run(self, task_name, days_threshold):
        """Check if time since last execution excedes threshold"""
        last_run = self.state.get(task_name) # get time in ISO string format

        if not last_run:
            return True # program has never runned before

        last_run_date = datetime.fromisoformat(last_run)
        days_since_run = (datetime.now() - last_run_date).days

        # return execution flag
        return days_since_run >= days_threshold

    def marked_complete(self, task_name):
        """Register task with current time when completed"""
        self.state[task_name] = datetime.now().isoformat()
        self.save_state()
    
    def check_and_clean(self):
        """Check and runn cleanup based on task intervalas"""
        # instantiate cleaner object
        cleaner = GmailCleaner()
        cleaning_update = False

        # tasks and their cleanup intervals
        tasks = {
            'old_emails': {
                'interval': 90,      # very 3 months 
                'action': lambda: cleaner.clean_old_emails(days_old=90),
            },
            'promotional': {
                'interval': 3,      # Every 3 days
                'action': lambda: cleaner.clean_promotional_emails(),
            },
            'spam': {
                'interval': 7,      # weekly
                'action': lambda: cleaner.clean_spam_emails(),
            },
            'large_emails': {
                'interval': 14,     # bi-weekly
                'action': lambda: cleaner.clean_large_emails(size_mb=15),
            },
            'empty_trash': {
                'interval': 60,      # every 2 months
                'action': lambda: cleaner.empty_trash(),
            }
        }
    
        # loop over task and check if cleaning is needed
        for task, task_info in tasks.items():
            # check if task needs to be performed
            if self.should_run(task, task_info["interval"]):
                
                # authenticat once and update flag 
                if not cleaning_update:
                    cleaner.authenticate()
                    cleaning_update = True

                # clean task and update time 
                task_info["action"]()
                self.state[task] = datetime.now().isoformat()
            
        # save state 
        if cleaning_update:
            self.save_state() 
        
        if  not cleaning_update:
            print("No cleaning needed at the momment")
                

