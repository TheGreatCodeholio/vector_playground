# Vector Playground

This is a webui that controls vector in a few different ways. 

1. Enables easier custom intents.
2. Takes full control of Vectors routines
3. Allows remote control via webui

Application Setup and Usage Guide
=================================

Prerequisites
-------------

Ensure you have the following installed on your system:

1.  **Git**: You will need `git` to clone the repository.
2.  **Python 3.x**: Make sure you have Python 3 installed. You can check your version by running:
    
    `python3 --version`
    
3.  **Python Package Installer (pip)**: `pip` is required to install Python packages. It is typically included with Python installations.

Steps to Install and Set Up
---------------------------

### 1\. Clone the Git Repository

Start by cloning the repository. In your terminal or command prompt, run:

`git clone https://github.com/TheGreatCodeholio/vector_playground.git`


### 2\. Navigate to the Project Directory

Once the repository is cloned, change your current directory to the project folder:

`cd vector_playground`

### 3\. Set Up a Python Virtual Environment

It is recommended to use a virtual environment to manage dependencies. Run the following commands to create and activate the virtual environment:

#### On Linux/macOS:

`python3 -m venv venv source venv/bin/activate`

#### On Windows:

`python -m venv venv venv\Scripts\activate`

You should now see `(venv)` in your terminal, indicating that the virtual environment is active.

### 4\. Install Dependencies

With the virtual environment activated, install the required Python packages listed in `requirements.txt`:

`pip install -r requirements.txt`

This command will install all necessary dependencies to run the application.

### 6\. Authenticate SDK with your Vector

`python -m anki_vector.configure`

when complete you will get a path like `Writing config file to '/home/user/.anki_vector/sdk_config.ini'` copy that path down

### 7\. Configure Vector Playground

Copy the `etc/sample_config` to `etc/config.json`

edit `config.json` to add the path to where `sdk_config.ini` is located. 
You can get this folder from the previous step.

```json
"sdk_config_path": "/home/user/.anki_vector",
```

### 8\. Running the Application

Once the setup is complete, you can start the application by running:

`python vector_playground.py`

Replace `vector_playground.py` with the name of the main Python script that launches your application.

