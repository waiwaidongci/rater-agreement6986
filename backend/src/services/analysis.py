from .validation import validate_config
from .counts import panel_counts
from .fleiss import fleiss,UndefinedKappa
from .bootstrap import row_bootstrap
from .pairs import pair_agreement
from .fingerprint import fingerprint

def analyze(study,specimens,votes,config):
 validate_config(config)
 rows,incomplete=panel_counts(study,specimens,votes,complete_only=True)
 if len(rows)<2:
  raise UndefinedKappa(f'齐票试样仅{len(rows)}个：三人Fleiss κ至少需要2个齐票试样（缺票试样已排除，缺票不是类别），本次运行不产出三人κ')
 matrix=[r['counts'] for r in rows]
 result=fleiss(matrix)
 for item,P in zip(rows,result['item_agreement']):item['agreement']=P
 bootstrap=row_bootstrap(matrix,config['bootstrap_repeats'],config['seed'])
 pairs=pair_agreement(study,specimens,votes,config['bootstrap_repeats'],config['seed'])
 coverage={'total_specimens':len(specimens),'complete_specimens':len(rows),'incomplete_specimens':len(incomplete),
  'total_votes':len(votes),'expected_votes':len(specimens)*3,'missing_votes':len(specimens)*3-len(votes),
  'incomplete_detail':incomplete,
  'policy':'三人Fleiss κ与整行bootstrap仅使用齐票试样；缺票试样保留在底稿并进入成对口径，缺票不是类别'}
 return {**result,'source_study':study,'categories':study['categories'],'raters':study['raters'],'items':rows,
  'coverage':coverage,'pair_agreement':pairs,
  'bootstrap':bootstrap,'fingerprint':fingerprint(study,specimens,votes,config),
  'interpretation':'Agreement relative to empirical category marginals, not accuracy against a gold standard. Fixed complete three-person panel; bootstrap resamples whole iid specimens, not votes or new raters. Missing-vote specimens are stored but excluded from Fleiss κ; pair-wise Cohen κ uses only specimens both raters voted on.'}
