from .validation import validate_source

def panel_counts(study,specimens,votes,complete_only=False):
 validate_source(study,specimens,votes);ordered=sorted(specimens,key=lambda s:s['reference']);categories=study['categories'];raters=study['raters'];lookup={s['id']:{} for s in ordered}
 for vote in votes:lookup[vote['specimen_id']][vote['rater']]=vote['category']
 rows=[];incomplete=[]
 for specimen in ordered:
  labels=lookup[specimen['id']];present=[r for r in raters if r in labels];missing=[r for r in raters if r not in labels]
  if missing:incomplete.append({'specimen_id':specimen['id'],'reference':specimen['reference'],'missing_raters':missing})
  if complete_only and missing:continue
  counts=[sum(labels.get(r)==c for r in raters) for c in categories]
  rows.append({'id':specimen['id'],'reference':specimen['reference'],'description':specimen['description'],'counts':counts,'votes':[{'rater':r,'category':labels.get(r),'missing':r not in labels} for r in raters],'missing_raters':missing})
 return rows,incomplete
