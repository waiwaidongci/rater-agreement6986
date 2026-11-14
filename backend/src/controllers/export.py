from fastapi import HTTPException
from src.models import ReviewMemo
from src.services.audit import record
from src.utils.csv_export import csv_response

def export_memo(db,id,actor):
 memo=db.get(ReviewMemo,id)
 if not memo:raise HTTPException(404,'说明不存在')
 if memo.status!='approved':raise HTTPException(409,'仅批准说明可导出')
 r=memo.result_snapshot;b=r['bootstrap'];ci=b['interval'];rows=[[memo.name,r['source_study']['name'],r['fingerprint'],r['kappa'],r['pbar'],r['pe'],b['valid_repeats'],b['invalid_repeats'],ci[0] if ci else '',ci[1] if ci else '',item['reference'],item['agreement'],str(item['counts']),memo.interpretation,memo.next_step,memo.review_note] for item in r['items']]
 record(db,actor,'memo.exported',{'memo_id':id});return csv_response(f'rater-review-{id}.csv',rows,['复核说明','研究','指纹','Fleissκ','Pbar','Pe','有效重复','退化重复','经验区间下限','经验区间上限','试样','逐项P','类别计数','人工解释','下一步','审核意见'])

def export_memo_pairs(db,id,actor):
 memo=db.get(ReviewMemo,id)
 if not memo:raise HTTPException(404,'说明不存在')
 if memo.status!='approved':raise HTTPException(409,'仅批准说明可导出')
 r=memo.result_snapshot;pa=r.get('pair_agreement')
 if not pa:raise HTTPException(409,'该冻结快照生成于成对口径上线前，无成对数据')
 rows=[]
 for p in pa['pairs']:
  bs=p['bootstrap'];ci=bs['interval'];head=[memo.name,r['source_study']['name'],p['rater_a'],p['rater_b'],p['included_count'],p['excluded_count'],p['kappa'] if p['computable'] else '',p.get('observed_agreement') if p.get('observed_agreement') is not None else '',p.get('chance_agreement') if p.get('chance_agreement') is not None else '',p['undefined_reason'] or '',bs['valid_repeats'],bs['invalid_repeats'],bs['valid_fraction'],ci[0] if ci else '',ci[1] if ci else '',bs['interval_status'],'纳入: '+'、'.join(p['included_references']),'排除: '+'；'.join(f"{e['reference']}(缺{'/'.join(e['missing_raters'])})" for e in p['excluded_specimens'])]
  rows.append(head)
 record(db,actor,'memo.exported_pairs',{'memo_id':id});return csv_response(f'rater-pairs-{id}.csv',rows,['复核说明','研究','标记者A','标记者B','纳入试样数','排除试样数','Cohenκ','观察一致率Po','机会一致率Pe','未定义原因','有效重复','退化重复','有效比例','区间下限','区间上限','区间状态','纳入试样编号','排除试样及缺票'])
