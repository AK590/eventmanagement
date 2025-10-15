create folders
frontend(index.html,main.js)
backend(rest of the files are all part of the backend)#__init__.py is an empty file created to pinpoint the location of the backend folder
STEPS TO RUN THE CODE:
'''Open Your Terminal: Open a command prompt or terminal window.'''
'''Navigate to Your Project Folder: Use the cd command to navigate to your main eventmanagement folder. This is the root folder that contains the backend and frontend directories.'''
Bash
cd C:\Users\admin\Desktop\eventmanagement

'''Create a Virtual Environment: Create an isolated Python environment for this project.'''
Bash
python -m venv venv

'''Activate the Environment: You must activate the environment every time you work on the project.'''
Bash
venv\Scripts\activate
'''Your terminal prompt should now change to show (venv) at the beginning.'''

'''Install All Dependencies: Install all the required libraries from your requirements.txt file.'''
Bash
pip install -r requirements.txt
'''Clean Slate (Optional but Recommended): For the dynamic pricing to work with the latest logic, delete the old model and database files from your backend folder:
   pricing_model.joblib
   event.db'''

'''Part 2: Running the Application (Do this every time)
Open Terminal and Navigate: Open a new terminal and navigate to your root eventmanagement folder.'''

Activate the Environment:
Bash
venv\Scripts\activate


'''Run the Server: From the root eventmanagement directory, run the uvicorn command exactly as follows:'''
Bash
uvicorn backend.main:app --reload
'''The terminal will show output indicating the server has started, ending with a line like Uvicorn running on http://127.0.0.1:8000.'''
