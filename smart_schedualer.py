import json 
import os
import argparse
from datetime import datetime, timedelta
from email_cleaner import GmailCleaner

class SmartScheduler:
    def __int__(self, state_file="gmail_cleaner_state.jason"):
        # task status initialization 
        self.state_file = state_file
        self.load_state()

        # initialize cleaner 
        self.cleaner = GmailCleaner()

        # task configurations: task + clening intervals + executable 
        self.tasks = {
            'old_emails': {
                'interval': 90,      # very 3 months 
                'action': lambda: self.cleaner.clean_old_emails(days_old=90),
            },
            'promotional': {
                'interval': 3,      # Every 3 days
                'action': lambda: self.cleaner.clean_promotional_emails(),
            },
            'spam': {
                'interval': 7,      # weekly
                'action': lambda: self.cleaner.clean_spam_emails(),
            },
            'large_emails': {
                'interval': 14,     # bi-weekly
                'action': lambda: self.cleaner.clean_large_emails(size_mb=15),
            },
            'empty_trash': {
                'interval': 60,      # every 2 months
                'action': lambda: self.cleaner.empty_trash(),
            }
        }

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
        # cleaning flag
        cleaning_update = False    

        # loop over task and check if cleaning is needed
        for task, task_info in self.tasks.items():
            # check if task needs to be performed
            if self.should_run(task, task_info["interval"]):
                
                # authenticat once and update flag 
                if not cleaning_update:
                    self.cleaner.authenticate()
                    cleaning_update = True

                # clean task and update time 
                task_info["action"]() # execute task 
                self.state[task] = datetime.now().isoformat()
            
        # save state 
        if cleaning_update:
            self.save_state() 
        
        if  not cleaning_update:
            print("No cleaning needed at the momment")

    def stats(self):
        """Display last execution of tasks """    
        print("Cleaning status: ")
        print("-" * 40 )

        # loop over tasks and  print out the last execution 
        for task in self.tasks.keys():
            last_run = self.state.get(task)
            if last_run:
                last_run_date = datetime.fromisoformat(last_run)
                days_ago = (datetime.now() - last_run_date).days
                print(f"{task:15} was executed {days_ago}\n on {last_run_date}")
            else: 
                print(f"{task:15} was never executed")

def main():
    # init agument parser
    parser = argparse.ArgumentParser(description="Smart Gmail Cleaner")

    # set argument for function to take 
    parser.add_argument("--check-run", action="store_true",
                        help="Check and run cleanup if needed")
    parser.add_argument("--status", action="store_true",
                        help="Show status of las cleanup runs")
    parser.add_argument("--force", action="store_true",
                        help="Force run all cleanup tasks")
    
    # parse arguments
    args = parser.parse_args()
    
    # inti schedualer
    scheduler = SmartScheduler()