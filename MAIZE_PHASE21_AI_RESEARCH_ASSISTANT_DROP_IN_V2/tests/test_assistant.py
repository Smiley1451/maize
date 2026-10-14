from app.assistant import ResearchAssistant

def test_router_routes_genotype():
    a=ResearchAssistant(); names=a.route('Tell me about MAH-22-17 yield and TLB')
    assert 'genotype_profile' in names and 'search_project_records' in names

def test_router_routes_pipeline():
    a=ResearchAssistant(); names=a.route('Why did Phase 12 fail?')
    assert 'project_file_search' in names

def test_chat_returns_grounded_structure():
    a=ResearchAssistant(); r=a.chat('What models are available in the project?')
    assert r['status']=='ok'; assert r['answer']; assert isinstance(r['tools_used'],list)

def test_missing_question_is_safe():
    a=ResearchAssistant(); r=a.chat('')
    assert r['status']=='ERROR'
