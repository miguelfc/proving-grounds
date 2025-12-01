import sys
import datetime

class LoggerTee:
    """
    Redirects stdout to both the terminal and a log file.
    """
    def __init__(self, filename="execution.log"):
        self.terminal = sys.stdout
        self.log_file = open(filename, "w", buffering=1) # Line buffered

    def write(self, message):
        self.terminal.write(message)
        # Add timestamp to non-empty messages in the log file
        if message.strip():
            timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S] ")
            self.log_file.write(f"{timestamp}{message}")
        else:
            self.log_file.write(message)

    def flush(self):
        self.terminal.flush()
        self.log_file.flush()

# Redirect stdout globally when this module is imported
if not isinstance(sys.stdout, LoggerTee):
    sys.stdout = LoggerTee()

class FrameworkLogger:
    def log(self, message: str):
        # Just print, which now goes to both console and file via LoggerTee
        print(message)
        
    def start_execution(self):
        print(f"\n{'='*40}")
        print(f"EXECUTION STARTED: {datetime.datetime.now().isoformat()}")
        print(f"{'='*40}\n")

    def end_execution(self):
        print(f"\n{'='*40}")
        print(f"EXECUTION ENDED: {datetime.datetime.now().isoformat()}")
        print(f"{'='*40}\n")

# Global instance
logger = FrameworkLogger()
