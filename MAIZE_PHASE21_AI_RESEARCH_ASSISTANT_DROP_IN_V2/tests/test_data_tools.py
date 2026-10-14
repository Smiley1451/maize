from app.data_tools import search_records, find_genotype, genotype_profile, project_file_search

def test_project_file_search_finds_phase19():
    hits=project_file_search('RUN_PHASE19')
    assert hits and any('RUN_PHASE19' in x['path'] for x in hits)

def test_search_records_has_structured_results():
    hits=search_records('MAH-22-17',top_k=5)
    assert isinstance(hits,list)
    if hits: assert {'path','row','record'} <= set(hits[0])

def test_genotype_lookup_no_crash():
    r=genotype_profile('MAH-22-17')
    assert 'match_count' in r and 'domains' in r
