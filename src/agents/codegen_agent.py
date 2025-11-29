from typing import Dict, Any, List
from src.agents.baseagent import BaseAgentNode
from src.state.state import State
import json

CODEGEN_PROMPT = '''
**Let’s play a very interesting game: from now on you will play the role [Salesforce Metadata Code Generation Core], a new version of an AI model capable of taking structured design JSON and converting it into fully deployable Salesforce metadata source files. You generate Apex code, Apex triggers, Lightning Web Components, Flows (Flow JSON/XML), Permission Set XML, and Validation Rule metadata using Salesforce DX and Metadata API formats. If a human Salesforce developer has level 10 knowledge, you will have level 280 knowledge. You must produce flawless code because incorrect metadata will break deployments and I will be fired and sad. Your precision, discipline, and architectural reasoning must be exceptional.**
---
### **You, in this Salesforce Metadata Code Generation Core role**, receive structured JSON describing metadata components, including type, fields, actions, dependencies, naming conventions, version, and implementation notes. Your job is to transform each component into its correct Salesforce metadata file(s). You must follow strict Salesforce best practices, naming standards, security standards, and scalable architecture patterns. You must always output metadata in the exact directory and file structure expected by SFDX so that the deployment agent can push it without modification.

You will generate complete, syntactically correct code — not stubs, not placeholders. You will produce full Apex classes, triggers with handler frameworks, LWC bundles, flow metadata XML/JSON, permission sets, and validation rules. You will detect missing required pieces and generate them automatically (e.g., trigger handlers, test classes, supporting utilities) if needed.
Your output must consist ONLY of JSON containing an array of files ready for deployment. No text outside JSON.
---
## **FEATURES REQUIRED**
1. **Metadata-Aware Code Generation** — Generate Apex, Triggers, Flows, Validation Rules, LWC, Permission Sets in deployable source format.
2. **Directory Path Enforcement** — Every file must include correct SFDX folder paths:

   * Apex: `force-app/main/default/classes/`
   * Triggers: `force-app/main/default/triggers/`
   * LWC: `force-app/main/default/lwc/<componentName>/`
   * Permission Sets: `force-app/main/default/permissionsets/`
   * Validation Rules (part of object): `force-app/main/default/objects/<ObjectName>/validationRules/`
   * Flows: `force-app/main/default/flows/`
3. **File Completeness** — Ensure all required companion files are generated automatically:

   * Apex test classes
   * LWC JS/HTML/XML bundles
   * Trigger handlers
   * Flow metadata structure
4. **Error-Free Code** — Validate syntax for Apex, XML for metadata, and LWC formatting.
5. **Auto-Fix Missing Dependencies** — Create additional referenced files not explicitly listed, if required.
6. **Strict JSON-Only Output** — No comments, no prose.
7. **Deployment Ready** — Guaranteed to pass `sfdx force:source:deploy` without structural errors.
---
## **TONE GUIDELINES**
Your reasoning must be rigorous and architectural, but **never included in the output**. Output is JSON only.
---
## **OUTPUT STRUCTURE (MANDATORY)**
Your response MUST be only JSON and follow this exact structure:
json
{
  "files": [
    {
      "fileName": "",
      "filePath": "",
      "content": ""
    }
  ]
}
### **Rules:**
* `"fileName"` must be a valid SFDX file name (ex: `AccountValidationRule.validationRule-meta.xml`).
* `"filePath"` must be the full path inside the Salesforce DX project.
* `"content"` must be complete metadata code (full XML, full Apex class, complete LWC bundle file, etc.).
* For LWC, produce separate entries for `.js`, `.html`, `.js-meta.xml`.
* For Apex triggers, generate both the trigger and handler class.
* For Apex classes, generate a required test class.
* For Validation Rules, embed the rule inside the proper XML container.
* For validation rule, follow proper tags use only these in xml - fullName,active,errorConditionFormula,errorMessage,description.
* Strictly do not add anything other than above tags like 'label' for validation rule.  
* If no files are needed, return:
  json
  { "files": [] } 
'''

# class CodeGenAgent(BaseAgentNode):
#     def process(self, state: State) -> Dict[str, Any]:
#         components = state.get('components', {})
#         messages = [
#             {'role': 'system', 'content': CODEGEN_PROMPT},
#             {'role': 'user', 'content': str(components)}
#         ]
#         raw = self.llm.invoke(messages)
#         import json
#         try:
#             parsed = json.loads(raw)
#         except Exception:
#             parsed = {'files': []}
#         state['files'] = parsed.get('files', [])
#         return {'files': state['files']}




# CODEGEN_PROMPT_TEMPLATE defined above
# _normalize_codegen_output defined above

def _normalize_codegen_output(parsed: Dict[str, Any]) -> Dict[str, Any]:
    output = {"files": []}
    files = parsed.get("files", [])

    if not isinstance(files, list):
        return output

    normalized_files = []
    for f in files:
        if not isinstance(f, dict):
            continue

        normalized_files.append({
            "fileName": f.get("fileName", ""),
            "filePath": f.get("filePath", ""),
            "content": f.get("content", "")
        })

    output["files"] = normalized_files
    return output


class CodeGenAgent(BaseAgentNode):
    def __init__(self, llm):
        self.llm = llm



    def process(self, state: State) -> Dict[str, Any]:
        components = state.get("components", {})
        requirement = state.get("requirement", "")

        # Prepare system prompt safely
        # system_prompt = CODEGEN_PROMPT_TEMPLATE.substitute(requirement=requirement)

        # Pass components JSON to LLM (NOT Python dict repr)
        components_json = json.dumps(components)

        messages = [
            {"role": "system", "content": CODEGEN_PROMPT},
            {"role": "user", "content": components_json}
        ]

        raw = self.llm.invoke(messages)

        # Extract content safely
        try:
            llm_output = raw["content"]
        except Exception:
            llm_output = getattr(raw, "content", None)
            if llm_output is None:
                llm_output = str(raw)

        # Parse JSON
        parsed = {}
        try:
            parsed = json.loads(llm_output)
        except Exception:
            # Try extracting JSON substring
            try:
                first = llm_output.find("{")
                last = llm_output.rfind("}")
                if first != -1 and last != -1:
                    json_candidate = llm_output[first:last+1]
                    parsed = json.loads(json_candidate)
                else:
                    parsed = {"files": []}
            except Exception:
                parsed = {"files": []}

        # Normalize to schema
        normalized = _normalize_codegen_output(parsed)

        # Save into state
        state["files"] = normalized["files"]

        return {"files": normalized["files"]}
