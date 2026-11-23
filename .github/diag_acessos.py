import json, os, urllib.request, urllib.parse
from datetime import datetime, timedelta, timezone
out = {}
def req(url, data=None, headers=None):
    r = urllib.request.Request(url, data=data, headers=headers or {}, method="POST" if data else "GET")
    try:
        with urllib.request.urlopen(r, timeout=40) as x: return json.loads(x.read().decode())
    except urllib.error.HTTPError as e: return {"_erro": e.code, "_corpo": e.read().decode()[:500]}
    except Exception as e: return {"_erro": repr(e)}
tok = os.environ.get("CF_TOKEN", ""); acc = os.environ.get("CF_ACC", "")
H = {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}
hoje = datetime.now(timezone.utc).date(); ini = (hoje - timedelta(days=30)).isoformat()
out["token"] = req("https://api.cloudflare.com/client/v4/user/tokens/verify", headers=H)
out["zonas"] = req("https://api.cloudflare.com/client/v4/zones?name=plantaoinforma.com.br", headers=H)
zid = ((out["zonas"].get("result") or [{}])[0] or {}).get("id")
def gql(q, v): return req("https://api.cloudflare.com/client/v4/graphql", json.dumps({"query": q, "variables": v}).encode(), H)
out["rum_sites"] = req(f"https://api.cloudflare.com/client/v4/accounts/{acc}/rum/site_info/list", headers=H)
out["rum"] = gql("""query($a:String!,$d:Date!){viewer{accounts(filter:{accountTag:$a}){
  dia:rumPageloadEventsAdaptiveGroups(limit:60,filter:{date_geq:$d},orderBy:[date_ASC]){count sum{visits} dimensions{date}}
  pais:rumPageloadEventsAdaptiveGroups(limit:15,filter:{date_geq:$d},orderBy:[count_DESC]){count sum{visits} dimensions{countryName}}
  pag:rumPageloadEventsAdaptiveGroups(limit:15,filter:{date_geq:$d},orderBy:[count_DESC]){count dimensions{requestPath}}
  ref:rumPageloadEventsAdaptiveGroups(limit:15,filter:{date_geq:$d},orderBy:[count_DESC]){count dimensions{refererHost}}
  disp:rumPageloadEventsAdaptiveGroups(limit:10,filter:{date_geq:$d},orderBy:[count_DESC]){count dimensions{deviceType}}
}}}""", {"a": acc, "d": ini})
if zid:
    out["zona_http"] = gql("""query($z:String!,$d:Date!){viewer{zones(filter:{zoneTag:$z}){
      httpRequests1dGroups(limit:31,filter:{date_geq:$d},orderBy:[date_ASC]){dimensions{date} sum{requests pageViews} uniq{uniques}}}}}""", {"z": zid, "d": ini})
# Telegram
tt = os.environ.get("TG", "")
if tt: out["telegram"] = req(f"https://api.telegram.org/bot{tt}/getChatMemberCount?chat_id=%40plantaodenoticias")
# Instagram
ig = os.environ.get("IG", "")
if ig:
    out["instagram"] = req("https://graph.instagram.com/v23.0/me?" + urllib.parse.urlencode({"fields": "username,followers_count,media_count", "access_token": ig}))
    out["ig_insights"] = req("https://graph.instagram.com/v23.0/me/insights?" + urllib.parse.urlencode({"metric": "reach,accounts_engaged,profile_views,website_clicks", "period": "day", "metric_type": "total_value", "since": int((datetime.now(timezone.utc)-timedelta(days=28)).timestamp()), "until": int(datetime.now(timezone.utc).timestamp()), "access_token": ig}))
# Podcast: downloads dos MP3 nas Releases
gh = os.environ.get("GH", ""); repo = os.environ.get("REPO")
rels = req(f"https://api.github.com/repos/{repo}/releases?per_page=20", headers={"Authorization": f"Bearer {gh}"})
pod = {}
if isinstance(rels, list):
    for r in rels:
        for a in r.get("assets", []): pod[a["name"]] = a["download_count"]
out["podcast"] = pod
json.dump(out, open("/tmp/out/acessos.json", "w"), ensure_ascii=False, indent=1)
