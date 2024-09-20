
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import json
from ouvrai import ouvrai as ou
import os

# Path to your service account key JSON file
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
        'databaseURL': 'https://neuronepal2-1440a-default-rtdb.firebaseio.com/'
    })

db_ref = db.reference('/experiments/mentalnavigation')


def get_participant_ids():
    all_keys = list(db_ref.get(shallow=True).keys())
    valid_keys = []
    for key in all_keys:
        data = db_ref.child(key).get()  # Fetch the actual data for each key
        if data['info'].get('completed',False):
            valid_keys.append(key)
    return valid_keys


def get_participant_data(uid):
    # uid = 'mFnnnES08wMZ1qR97SxgzjX8xWH2'
    db_ref = db.reference(f'/experiments/mentalnavigation/{uid}')
    file_path = f'data/{uid}.json'

    # with open(file_path, 'w') as json_file:
    #     json.dump({uid:db_ref.get()}, json_file)
    data = {uid:db_ref.get()}
    data_folder = 'data/'
    trial, subject, frame, state = ou.load(
                data_folder=data_folder,
                file_regex=f"^{uid}.json",
                exp_data=data,
            )

    return trial,subject,frame,state