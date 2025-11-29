from typing import Dict, Any
from src.agents.baseagent import BaseAgentNode
from src.state.state import State
from string import Template

REQ_SYSTEM_PROMPT_TPL = Template('''
You are a Salesforce Solution Architect. Read the following requirement carefully.
Identify: 1. Business domain (Sales, Service, CPQ, Marketing, Platform)
   2. Core objects involved 3. Key actions or changes (create, modify, delete, automate, integrate)
   4. Any integrations or UI changes.
   Note: The domain will always be salesforce
Return output in JSON: {"Original requirement":"", "domain": "", "objects": [], "actions": [], "integrationPoints": [] }
See Sample Example Output format below
{"Original requirement":"Add a simple validation to check if owner exists in an opportunity", "domain": "Salesforce", "objects": ["Quote", "Quote Line Item"], "actions": ["Add validation rule", "Update approval flow"], "integrationPoints": [], "clarificationsNeeded": ["Does it apply to renewal quotes?"] }
''')

class ReqAgent(BaseAgentNode):
    def __init__(self, llm):
        self.llm = llm

    def process(self, state: State) -> Dict[str, Any]:
        requirement = state.get('requirement', '')

        prompt = REQ_SYSTEM_PROMPT_TPL.substitute(requirement=requirement)
        messages = [
            {'role': 'system', 'content': prompt},
            {'role': 'user', 'content': requirement}
        ]

        # Call LLM
        raw = self.llm.invoke(messages)
        print("raw*******************")
        print(raw)

        # Extract actual text content
        try:
            # for LangChain & most LLM wrappers
            llm_output = raw["content"]
        except:
            # fallback
            llm_output = raw.content if hasattr(raw, "content") else str(raw)

        print("llm_output -----------")
        print(llm_output)

        # Parse JSON
        import json
        try:
            parsed = json.loads(llm_output)
        except Exception as e:
            print("JSON parse error:", e)
            parsed = {
                "domain": "",
                "objects": [],
                "actions": [],
                "integrationPoints": [],
                "clarificationsNeeded": []
            }

        state['breakdown'] = parsed
        return {'breakdown': parsed}
