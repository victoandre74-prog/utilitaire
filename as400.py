import pyodbc

try:
    conn = pyodbc.connect(
        "DSN=commercial;"
        "UID=vandre;"
        "PWD=107Fanfoue$1;"
    )

    print("Connexion réussie")
    conn.close()
    
    print("Connexion fermée")

except Exception as e: 
    print("Connexion refusée") 
    print(e)   
