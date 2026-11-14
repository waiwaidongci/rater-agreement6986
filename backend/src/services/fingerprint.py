import hashlib,json
VERSION='fixed-panel-fleiss-row-bootstrap-v2'
def fingerprint(study,specimens,votes,config):
 payload={'version':VERSION,'study':study,'specimens':sorted(specimens,key=lambda s:s['reference']),'votes':sorted(votes,key=lambda v:(v['specimen_id'],v['rater'])),'config':config,'missing_vote_policy':'absent votes excluded from Fleiss and pair Cohen kappa; absence is not a category'}
 return hashlib.sha256(json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
