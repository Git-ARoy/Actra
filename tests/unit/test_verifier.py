import pytest
from unittest.mock import patch
from actra.agent.verifier import Verifier
from actra.models import ToolResult, Task

def test_action_verification():
    verifier = Verifier()
    
    ok_res = ToolResult.ok('safari_search', query='iqoo15', url='https://google.com')
    assert verifier.verify_action('safari_search', ok_res) is True
    
    fail_res = ToolResult.fail('safari_search', 'ERROR', 'network failed')
    assert verifier.verify_action('safari_search', fail_res) is False

def test_goal_verification_safari():
    verifier = Verifier()
    task = Task(goal='Open Safari and search for iQOO 15')
    task.tool_calls = [
        {
            'tool': 'open_application',
            'result': {'success': True}
        },
        {
            'tool': 'safari_search',
            'result': {'success': True, 'data': {'url': 'https://google.com/search?q=iQOO+15'}}
        }
    ]
    
    with patch('actra.mac.apple_events.list_running_apps', return_value=['Safari', 'Finder']),          patch('actra.mac.apple_events.run_applescript', side_effect=['https://google.com/search?q=iQOO+15', 'iQOO 15 - Google Search']):
        res = verifier.verify_goal(task)
        assert res.verified is True
        assert len(res.checks) == 3
        assert all(c.passed for c in res.checks)
