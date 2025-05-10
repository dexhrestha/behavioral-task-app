
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import json
from ouvrai import ouvrai as ou
import os
import pandas as pd

firebase_credentials = {
    "type": "service_account",
    "project_id": os.getenv("FIREBASE_PROJECT_ID"),
    "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
    "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace("\\n", "\n"),
    "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
    "client_id": os.getenv("FIREBASE_CLIENT_ID"),
    "auth_uri": os.getenv("FIREBASE_AUTH_URI"),
    "token_uri": os.getenv("FIREBASE_TOKEN_URI"),
    "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_CERT_URL"),
    "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT_URL")
}

cred = credentials.Certificate(firebase_credentials)

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://neuronepal-74c39-default-rtdb.firebaseio.com/'
    })



def get_participant_ids(project_name):
    db_ref = db.reference(f'/experiments/{project_name}')
    all_keys = list(db_ref.get(shallow=True).keys())
    valid_keys = []
    for key in all_keys:
        data = db_ref.child(key).get()  # Fetch the actual data for each key
        if data['info'].get('completed',False):
            valid_keys.append(key)
    return valid_keys

def download_participant_data(project_name,uid):
    if not uid:
        return False
    
    file_path = f'data_{project_name}/{uid}.json'
    
    if not os.path.exists(os.path.dirname(file_path)):
        os.mkdir(os.path.dirname(file_path))

    if not os.path.exists(file_path):
        db_ref = db.reference(f'/experiments/{project_name}/{uid}')
        data = {uid:db_ref.get()}
        if uid and data.get(uid):
            with open(file_path, 'w',encoding='utf-8') as json_file:
                json.dump(data, json_file, indent = 4, ensure_ascii = False)
        else:
            return False
    return file_path

def get_participant_data(project_name,uid):

    json_path = download_participant_data(project_name,uid)

    assert os.path.exists(json_path), "Participant data not found"

    trial = pd.DataFrame()
    subject = pd.DataFrame()
    frame = pd.DataFrame()
    state = pd.DataFrame()
    
    try:
        with open(json_path, 'r') as json_file:
            data= json.load(json_file)
            trial,subject,frame,state = ou.load(exp_data=data)
    except Exception as e :
        print("Cannot read file. Error :" + str(e))

    return trial,subject,frame,state

    