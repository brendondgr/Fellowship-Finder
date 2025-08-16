import os
import json
import re
import getpass

class FileManager:
    def __init__(self):
        self.root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.tmp_folder = os.path.join(self.root_dir, 'tmp')
        self.configs_folder = os.path.join(self.root_dir, 'configs')
        self.login_file = os.path.join(self.configs_folder, 'login.json')
        self.data_folder = os.path.join(self.root_dir, 'data')

    def setup(self):
        self.create_required_folders()
        self.check_login_credentials()

    def create_required_folders(self):
        if not os.path.exists(self.tmp_folder):
            os.makedirs(self.tmp_folder)
            print(f"Created folder: {self.tmp_folder}")

        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder)
            print(f"Created folder: {self.data_folder}")

    def is_valid_email(self, email):
        # Basic email validation regex
        regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(regex, email)

    def check_login_credentials(self):
        if not os.path.exists(self.login_file):
            print("Login credentials not found in configs/login.json.")
            email = ""
            while not self.is_valid_email(email):
                email = input("Enter your Profellow email: ")
                if not self.is_valid_email(email):
                    print("Invalid email format. Please try again.")
            
            password = getpass.getpass("Enter your Profellow password: ")

            credentials = {
                "email": email,
                "password": password
            }

            with open(self.login_file, 'w') as f:
                json.dump(credentials, f, indent=4)
            print(f"Credentials saved to {self.login_file}")

    def clear_tmp_folder(self):
        if os.path.exists(self.tmp_folder):
            for filename in os.listdir(self.tmp_folder):
                file_path = os.path.join(self.tmp_folder, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        import shutil
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f"Failed to delete {file_path}. Reason: {e}")
            print(f"Cleared contents of: {self.tmp_folder}")
        else:
            print(f"tmp folder does not exist: {self.tmp_folder}")

    def clear_data_folder(self):
        if os.path.exists(self.data_folder):
            for filename in os.listdir(self.data_folder):
                file_path = os.path.join(self.data_folder, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        import shutil
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f"Failed to delete {file_path}. Reason: {e}")
            print(f"Cleared contents of: {self.data_folder}")
        else:
            print(f"data folder does not exist: {self.data_folder}")