#!/usr/bin/env python3
"""Puppy50 v90 Firefox idle prelaunch A/B. Preserve sandbox, Fission and TLS."""
import argparse,json
from pathlib import Path
PREF="dom.ipc.processPrelaunch.enabled"
def patch(root):
    root=Path(root)
    fx=root/"usr/lib/firefox-esr"
    session=root/"usr/local/bin/puppy50-web-launch"
    if not fx.is_dir() or not session.is_file() or "firefox-esr" not in session.read_text():
        raise ValueError("Missing actual browser or original launch script")
    path=fx/"distribution/policies.json"
    current=json.loads(path.read_text()) if path.exists() else {"policies":{}}
    if not isinstance(current,dict) or not isinstance(current.get("policies"),dict):
        raise ValueError("Malformed existing policy")
    existing=current["policies"].setdefault("Preferences",{})
    if not isinstance(existing,dict) or PREF in existing:
        raise ValueError("Conflicting prelaunch preference; fail closed")
    existing[PREF]={"Value":False,"Status":"locked","Type":"boolean"}
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(current,indent=2,sort_keys=True)+"\n")
    check=json.loads(path.read_text())
    assert check["policies"]["Preferences"][PREF]["Value"] is False
    return {"schema":"PUPPY50_V90_SAFE_PRELAUNCH_EXPERIMENT","changed":[PREF],
      "prelaunch_enabled":False,"existing_policies_preserved":True,
      "fission_disabled":False,"sandbox_disabled":False,"certificate_checks_disabled":False}
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("root",type=Path);a=p.parse_args()
    print(json.dumps(patch(a.root),indent=2))
