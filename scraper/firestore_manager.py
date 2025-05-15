from google.cloud import firestore
import os

# Se necessário, defina o caminho do arquivo de credenciais do Google Cloud:
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "database/key.json"

_db = None

def get_firestore_client():
    """
    Retorna uma instância singleton do cliente Firestore.
    """
    global _db
    if _db is None:
        _db = firestore.Client()
    return _db

# Exemplo de uso direto (remova ou adapte em produção):
if __name__ == "__main__":
    db = get_firestore_client()
    print("Coleções disponíveis:")
    for collection in db.collections():
        print(collection.id)
