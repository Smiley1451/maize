from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)

def test_health():
    r=client.get('/health'); assert r.status_code==200 and r.json()['status']=='ok'

def test_status():
    r=client.get('/api/v1/assistant/status'); assert r.status_code==200

def test_tools():
    r=client.get('/api/v1/assistant/tools'); assert r.status_code==200 and 'tools' in r.json()

def test_models():
    r=client.get('/api/v1/assistant/models'); assert r.status_code==200 and 'items' in r.json()

def test_search():
    r=client.post('/api/v1/assistant/search',json={'query':'maize','top_k':3}); assert r.status_code==200

def test_chat():
    r=client.post('/api/v1/assistant/chat',json={'question':'What is Phase 19?'}); assert r.status_code==200; assert r.json()['answer']

def test_empty_chat_rejected():
    r=client.post('/api/v1/assistant/chat',json={'question':''}); assert r.status_code==422

def test_source_search():
    r=client.get('/api/v1/assistant/sources',params={'query':'Phase 19'}); assert r.status_code==200

def test_prediction_endpoint_contract():
    payload={'domain':'yield','features':{'genotype':'TEST','days_to_50_percent_pollen_shedding':70,'days_to_50_percent_silking':72,'days_to_75_percent_dry_husk':112,'plant_height':220,'ear_height':110,'plant_stand':70000,'shelling_percentage':82}}
    r=client.post('/api/v1/assistant/predict',json=payload); assert r.status_code==200; assert r.json()['status'] in {'ok'}
