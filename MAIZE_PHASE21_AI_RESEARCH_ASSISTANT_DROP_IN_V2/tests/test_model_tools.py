from app.model_tools import available_models, model_detail

def test_model_inventory_no_crash():
    rows=available_models(); assert isinstance(rows,list)

def test_model_rows_shape():
    rows=available_models()
    if rows: assert {'path','filename','kind','size_bytes'} <= set(rows[0])

def test_model_detail_no_crash():
    rows=available_models()
    if rows:
        r=model_detail(rows[0]['path']); assert 'available' in r and 'path' in r
