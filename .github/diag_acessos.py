import json, os, urllib.request
from datetime import datetime, timedelta, timezone
tok = os.environ["CF_TOKEN"]; acc = os.environ["CF_ACC"]
H = {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}
ini = (datetime.now(timezone.utc).date() - timedelta(days=30)).isoformat()
q = """query($a:String!,$d:Date!){viewer{accounts(filter:{accountTag:$a}){
 br:rumPageloadEventsAdaptiveGroups(limit:40,filter:{date_geq:$d,countryName:"BR"},orderBy:[date_ASC]){count sum{visits} dimensions{date}}
 brdisp:rumPageloadEventsAdaptiveGroups(limit:5,filter:{date_geq:$d,countryName:"BR"},orderBy:[count_DESC]){count sum{visits} dimensions{deviceType}}
 brref:rumPageloadEventsAdaptiveGroups(limit:10,filter:{date_geq:$d,countryName:"BR"},orderBy:[count_DESC]){count dimensions{refererHost}}
 brpag:rumPageloadEventsAdaptiveGroups(limit:15,filter:{date_geq:$d,countryName:"BR"},orderBy:[count_DESC]){count dimensions{requestPath}}
 brcid:rumPageloadEventsAdaptiveGroups(limit:15,filter:{date_geq:$d,countryName:"BR"},orderBy:[count_DESC]){count sum{visits} dimensions{userAgentBrowser userAgentOS}}
}}}"""
r = urllib.request.Request("https://api.cloudflare.com/client/v4/graphql", json.dumps({"query": q, "variables": {"a": acc, "d": ini}}).encode(), H)
try:
    with urllib.request.urlopen(r, timeout=40) as x: out = json.loads(x.read().decode())
except urllib.error.HTTPError as e: out = {"erro": e.read().decode()[:800]}
json.dump(out, open("/tmp/out/acessos.json", "w"), ensure_ascii=False, indent=1)
