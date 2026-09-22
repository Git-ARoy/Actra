import pytest
from unittest.mock import patch, MagicMock
from actra.llm.base import Message, ToolCall, ToolSchema
from actra.llm.ollama_provider import OllamaProvider, _repair_json_arguments, _extract_text_tool_calls

def test_repair_json_arguments():
    assert _repair_json_arguments({'a': 1}) == {'a': 1}
    assert _repair_json_arguments('{"name": "Safari"}') == {'name': 'Safari'}
    # trailing comma
    assert _repair_json_arguments('{"name": "Safari",}') == {'name': 'Safari'}
    assert _repair_json_arguments('') == {}

def test_extract_text_tool_calls():
    text = '<tool_call>{"name": "open_application", "arguments": {"name": "Safari"}}</tool_call>'
    calls = _extract_text_tool_calls(text)
    assert len(calls) == 1
    assert calls[0].name == 'open_application'
    assert calls[0].arguments == {'name': 'Safari'}

def test_ollama_provider_chat_mock():
    provider = OllamaProvider(model_name='gemma4:12b-mlx')
    
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        'message': {
            'content': '',
            'tool_calls': [
                {
                    'function': {
                        'name': 'open_application',
                        'arguments': {'name': 'Safari'}
                    }
                }
            ]
        }
    }
    
    with patch('httpx.Client.post', return_value=mock_resp):
        messages = [Message(role='user', content='Open Safari')]
        tools = [ToolSchema(name='open_application', description='Open app', parameters={'type': 'object'})]
        res = provider.chat(messages, tools)
        
        assert len(res.tool_calls) == 1
        assert res.tool_calls[0].name == 'open_application'
        assert res.tool_calls[0].arguments == {'name': 'Safari'}
