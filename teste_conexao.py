import firebase_admin
from firebase_admin import credentials, db

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://marialobato-v1-default-rtdb.firebaseio.com"
})

ref = db.reference("palestra/20270102")
palestra = ref.get()
print(palestra)