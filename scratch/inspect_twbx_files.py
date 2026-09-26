import zipfile

with zipfile.ZipFile(r'C:\Users\User\Documents\Superstore_Ellen_Blackburn_Edition.twbx', 'r') as z:
    for info in z.infolist():
        print(info.filename, info.file_size, info.date_time)
