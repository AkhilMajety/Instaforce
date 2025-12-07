import os
import subprocess
import json
import xml.etree.ElementTree as ET
import sys
import shutil
from typing import Dict, Any, List
from src.state.state import State
from src.agents.baseagent import BaseAgentNode
from dotenv import load_dotenv

load_dotenv()	

class DeployAgent(BaseAgentNode):
    

    def process(self, state: State) -> Dict[str, Any]:
        # ---------------------------------------------------------
        # USE FULL PATH TO SF CLI (FIX FOR WINDOWS)
        # ---------------------------------------------------------

        SF_EXE = r"C:\Users\MAkhil\AppData\Roaming\npm\sf.cmd"

        if not os.path.exists(SF_EXE):
            print(f"[ERROR] sf CLI not found at: {SF_EXE}")
            print("Run: where sf  — to verify path")
            sys.exit(1)

        print(f"[OK] Using Salesforce CLI at: {SF_EXE}")

        # ---------------------------------------------------------
        # CHECK FOR ORG ALIAS
        # ---------------------------------------------------------

        SF_USERNAME_ALIAS = os.environ.get("SF_USERNAME_ALIAS")

        if not SF_USERNAME_ALIAS:
            print("[ERROR] Please set SF_USERNAME_ALIAS environment variable")
            print("Example (PowerShell):")
            print('$env:SF_USERNAME_ALIAS = "trailhead"')
            sys.exit(1)

        # ---------------------------------------------------------
        # WRITE FILES TO deploy/force-app
        # ---------------------------------------------------------

        # DEPLOY_ROOT = "deploy"
        # FORCE_APP_ROOT = os.path.join(DEPLOY_ROOT, "force-app", "main", "default")

        DEPLOY_ROOT = "force-app"
        FORCE_APP_ROOT = os.path.join(DEPLOY_ROOT ,"main", "default")

        # Check if force-app folder exists and clean it before deployment
        if os.path.exists(DEPLOY_ROOT):
            print(f"[INFO] Removing existing force-app folder: {DEPLOY_ROOT}")
            shutil.rmtree(DEPLOY_ROOT)
            print(f"[OK] Removed {DEPLOY_ROOT}")

        os.makedirs(FORCE_APP_ROOT, exist_ok=True)
        # files =state["files"]
        files = state.get("files", {})

        written_files = []

        for f in files:
            rel_path = f["filePath"]
            fname = f["fileName"]
            full_path = os.path.join(DEPLOY_ROOT, rel_path, fname)

            # Validate content based on file type
            file_ext = os.path.splitext(fname)[1].lower()
            
            if file_ext in ['.xml', '.object', '.layout', '.profile', '.permissionset']:
                # Validate XML files
                try:
                    ET.fromstring(f["content"])
                    print(f"[OK] XML validated: {fname}")
                except ET.ParseError as e:
                    print(f"[ERROR] Invalid XML: {fname}\n{e}")
                    sys.exit(1)
            elif file_ext in ['.cls', '.trigger']:
                # Validate Apex files - basic check for non-empty content
                if not f["content"].strip():
                    print(f"[ERROR] Empty Apex file: {fname}")
                    sys.exit(1)
                print(f"[OK] Apex file validated: {fname}")
            elif file_ext in ['.js', '.cmp', '.app', '.evt']:
                # Lightning/Aura components - basic check
                if not f["content"].strip():
                    print(f"[ERROR] Empty component file: {fname}")
                    sys.exit(1)
                print(f"[OK] Component file validated: {fname}")
            else:
                # Generic validation for other files
                if not f["content"].strip():
                    print(f"[WARN] Empty file: {fname}")
                print(f"[OK] File validated: {fname}")

            os.makedirs(os.path.dirname(full_path), exist_ok=True)

            with open(full_path, "w", encoding="utf-8") as fh:
                fh.write(f["content"])

            print(f"[WRITE] {full_path}")
            written_files.append(full_path)

        # ---------------------------------------------------------
        # VALIDATE DEPLOY
        # ---------------------------------------------------------

        validate_cmd = [
            SF_EXE, "project", "deploy", "start",
            "-o", SF_USERNAME_ALIAS,
            # "-x", package_xml_path,
            # Use the root force-app folder directly; avoid force-app/force-app duplication
            "-d", DEPLOY_ROOT,
            "-w", "60",
            "--json"
        ]

        print("[INFO] Running validation:")
        print(" ".join(validate_cmd))

        result = subprocess.run(validate_cmd, capture_output=True, text=True)

        print("\n----- SF CLI STDOUT -----\n")
        print(result.stdout)

        print("\n----- SF CLI STDERR -----\n")
        print(result.stderr)

        try:
            parsed = json.loads(result.stdout)
            print("\n[Parsed JSON keys]", parsed.keys())
        except:
            parsed = None
            print("[WARN] Could not parse CLI JSON")

        deploy_status = {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "parsed_response": parsed,
            "written_files": written_files,
            "deploy_command": " ".join(validate_cmd)
        }

        if result.returncode == 0:
            print("\n[SUCCESS] Validation completed without blocking errors.")
            print(f"To deploy for real:\n\n{SF_EXE} project deploy start -o {SF_USERNAME_ALIAS} -x deploy/package.xml -d deploy/force-app -w 60 --json\n")
            deploy_status["message"] = "Deployment validation successful"
        else:
            print("\n[FAILED] Validation failed. Check errors above.")
            deploy_status["message"] = "Deployment validation failed"
        
        return {"deploy_status": deploy_status}
