from pathlib import Path
from app.parsers import chunk_text, parse_csv_rows

def test_chunk_text_overlap():
    text='a '*2000
    chunks=chunk_text(text,100,20)
    assert len(chunks)>1

def test_csv_parser_includes_header(tmp_path):
    p=tmp_path/'x.csv'
    p.write_text('a,b\n1,2\n3,4\n',encoding='utf-8')
    rows=list(parse_csv_rows(p,10))
    assert rows[0][0]==1 and 'CSV HEADER' in rows[0][1]
    assert any('a=1' in x[1] for x in rows)
