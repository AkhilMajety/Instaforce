import json
import re
from typing import Dict, Any, List
from src.agents.baseagent import BaseAgentNode
from src.state.state import State

# NOTE: This prompt contains many literal braces and must NOT be fed through str.format().
# We keep it as a raw triple-quoted string and DO NOT call .format() on it.
DESIGN_PROMPT = r'''
You, as the Salesforce Technical Architect Intelligence Core, will deeply analyze free-text requirements submitted by business users and identify all Salesforce metadata components implied by the described behavior. You will consider automation needs, UI implications, permissions, validation logic, integration points, and record lifecycle behaviors. You will have super results in metadata classification, estimation accuracy, and architectural reasoning. You will always enforce Salesforce naming conventions, best practices, modular patterns, versioning standards, and declarative-before-code principles.

Your main goal is to compute a precise JSON describing every required metadata component. Your task is to break down requirements into components, evaluate dependencies, calculate hours using LOW complexity assumptions, and output ONLY valid JSON. This JSON will be used directly by the Code Agent, so correctness and structure accuracy are mandatory.
To make this work, you must perform multi-pass reasoning, examine implicit needs, identify supporting metadata like Permission Sets, consider trigger handler frameworks, analyze user experience flows, and ensure consistent output structure. The JSON must always be syntactically correct, strict, and contain no explanation text.

FEATURES (AT LEAST 7)

Metadata Detection Engine – identify Flows, Apex Classes, Apex Triggers, LWCs, Validation Rules, Permission Sets.

Implicit Requirement Inference – detect hidden dependencies such as field-level security, supporting automation, or UI elements.

LOW-Complexity Hours Mapping – consistently assign LOW-effort hour values for each component.

Architecture Best Practices – enforce scalable, maintainable solutions only.

Naming & Version Standards – ensure output components follow Salesforce architectural naming.

Two-Stage Reasoning Pass – first identify components, then re-check for missing dependencies.

Strict JSON Enforcement – output MUST be JSON, no commentary, no Markdown.

Code Agent Ready Output – JSON must be directly consumable.

Empty Response Rule – if no components apply, return { "components": [] }.

TONE GUIDELINES

Reasoning must be technical, structured, and architect-grade—but must NEVER appear in output. Output is JSON only.

TIPS FOR BEST RESULTS

Infer missing metadata based on standard Salesforce implementation logic.

When unclear, choose the most scalable or standard solution path.

Validate JSON before output.

Always maintain strict field names: type, object, name, detail.

MANDATORY OUTPUT STRUCTURE (NO EXCEPTIONS)

The final output must be ONLY JSON and MUST follow this schema:
{
  "components": [
    {
      "type": "Flow | ApexClass | ApexTrigger | LWC | PermissionSet | ValidationRule",
      "apiName": "string",
      "label": "string",
      "object": "string or null",
      "description": "High-level functional purpose",
      "businessRequirement": "Full text of the requirement this component satisfies",
      "complexity": "Low",
      "estimatedHours": 0,

      "fields": [
        {
          "fieldName": "",
          "fieldApiName": "",
          "dataType": ""
        }
      ],

      "actions": [
        {
          "actionType": "create | update | delete | validation | screen | callApex | decision | assignment",
          "target": "target object or variable",
          "logic": "Description of logic conditions"
        }
      ],

      "dependencies": {
        "requiresPermissionSet": true,
        "requiredPermissionSetNames": [],
        "requiresApex": false,
        "requiredApexClasses": [],
        "requiresLWC": false,
        "requiredLWCs": []
      },

      "namingConventions": {
        "apiNameFormat": "",
        "version": 1
      },

      "implementationNotes": [
        "Architectural or design considerations for code agent"
      ]
    }
  ],

  "summary": {
    "totalComponents": 0,
    "totalEstimatedHours": 0,
    "assumptions": [
      "Any assumptions made by the design agent"
    ]
  }
}
Rules:

Return ONLY valid JSON.

Do NOT include text outside JSON.

If no components apply, return:
{ "components": [] }
'''

# Helper: ensure each component includes all required keys and defaults
def _normalize_component(cmp_obj: Dict[str, Any], default_business_req: str) -> Dict[str, Any]:
    # required top-level fields for each component per schema
    req_keys = {
        "type": None,
        "apiName": "",
        "label": "",
        "object": None,
        "description": "",
        "businessRequirement": default_business_req,
        "complexity": "Low",
        "estimatedHours": 0,
        "fields": [],
        "actions": [],
        "dependencies": {
            "requiresPermissionSet": False,
            "requiredPermissionSetNames": [],
            "requiresApex": False,
            "requiredApexClasses": [],
            "requiresLWC": False,
            "requiredLWCs": []
        },
        "namingConventions": {
            "apiNameFormat": "",
            "version": 1
        },
        "implementationNotes": []
    }

    normalized = {}
    for k, default in req_keys.items():
        if k in cmp_obj:
            normalized[k] = cmp_obj[k]
        else:
            # deep copy of default for mutable entries
            normalized[k] = json.loads(json.dumps(default))
    # Ensure types for some fields
    if not isinstance(normalized["fields"], list):
        normalized["fields"] = []
    if not isinstance(normalized["actions"], list):
        normalized["actions"] = []
    if not isinstance(normalized["implementationNotes"], list):
        normalized["implementationNotes"] = []
    # basic normalization for complexity and estimatedHours
    normalized["complexity"] = normalized.get("complexity", "Low") or "Low"
    try:
        normalized["estimatedHours"] = int(normalized.get("estimatedHours", 0))
    except Exception:
        normalized["estimatedHours"] = 0
    return normalized

# Validate top-level output structure; attempt to coerce if LLM misses 'summary'
def _normalize_output(parsed: Dict[str, Any], default_business_req: str) -> Dict[str, Any]:
    output = {"components": []}
    comps = parsed.get("components") if isinstance(parsed, dict) else None
    if not isinstance(comps, list):
        # maybe LLM returned single component object
        if isinstance(parsed, dict) and any(k in parsed for k in ("type", "apiName")):
            comps = [parsed]
        else:
            comps = []
    # normalize each component
    normalized_components = []
    for c in comps:
        if not isinstance(c, dict):
            continue
        normalized_components.append(_normalize_component(c, default_business_req))
    output["components"] = normalized_components

    # summary: compute totals if not present
    total_hours = sum(c.get("estimatedHours", 0) for c in normalized_components)
    total_components = len(normalized_components)
    summary = parsed.get("summary", {})
    if not isinstance(summary, dict):
        summary = {}
    summary.setdefault("totalComponents", total_components)
    summary.setdefault("totalEstimatedHours", total_hours)
    summary.setdefault("assumptions", summary.get("assumptions", []))
    output["summary"] = summary
    return output


class DesignAgent(BaseAgentNode):
    """
    DesignAgent - uses the DESIGN_PROMPT above to instruct the LLM to output strict JSON
    following the mandatory schema. This agent:
      - sends the breakdown JSON to the LLM (as machine-readable JSON)
      - extracts the LLM content safely from the wrapper object
      - parses JSON and normalizes/coerces it to the required schema
      - ensures a deterministic 'components' array and computed summary
      - returns {'components': parsed_output}
    """
    def __init__(self, llm):
        self.llm = llm

    def process(self, state: State) -> Dict[str, Any]:
        breakdown = state.get("breakdown", {})
        original_requirement = state.get('requirement', '')

        # ensure we send JSON, not Python repr
        try:
            breakdown_json = json.dumps(breakdown)
        except Exception:
            breakdown_json = "{}"

        messages = [
            {"role": "system", "content": DESIGN_PROMPT},
            # user content is JSON text of the requirement breakdown
            {"role": "user", "content": breakdown_json}
        ]

        print("breakdown$$$$$$$$$$")
        print(breakdown)
        print(breakdown_json)
        raw = self.llm.invoke(messages)

        print("design -********************raw")
        print(raw)
        # Extract LLM content robustly
        try:
            # common wrappers return dict-like or object with ["content"]
            llm_output = raw["content"]
        except Exception:
            llm_output = getattr(raw, "content", None)
            if llm_output is None:
                llm_output = str(raw)

        # Try to find first JSON object in LLM output if the entire output is not pure JSON
        parsed = {}
        try:
            parsed = json.loads(llm_output)
        except Exception:
            # attempt to extract JSON substring
            try:
                # find first {...} or [ ... ] block (greedy balanced-brace extraction)
                # simple approach: locate first { and last } and attempt to load substring
                first_brace = llm_output.find("{")
                last_brace = llm_output.rfind("}")
                if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                    candidate = llm_output[first_brace:last_brace+1]
                    parsed = json.loads(candidate)
                else:
                    # fallback: empty components
                    parsed = {"components": []}
            except Exception:
                parsed = {"components": []}

        # Normalize/coerce to exact schema and compute summary if missing
        normalized = _normalize_output(parsed, default_business_req=original_requirement)

        # Save to state and return
        state["components"] = normalized
        # Return the full normalized JSON structure (Code Agent expects this)
        return {"components": normalized}
