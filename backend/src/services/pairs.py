from fractions import Fraction
from itertools import combinations
import random

class UndefinedCohenKappa(ValueError):pass

MIN_PAIR_SPECIMENS=2

def _fraction_or_none(value):
 return None if value is None else float(value)

def cohen_kappa(pairs,categories):
 # pairs: 非空 (rater_a_category, rater_b_category) 元组列表，仅含两位标记者共同有票的试样
 n=len(pairs)
 if n<MIN_PAIR_SPECIMENS:
  raise UndefinedCohenKappa(f'共同有票试样不足{MIN_PAIR_SPECIMENS}个（实际{n}个），Cohen κ无法计算')
 index={c:i for i,c in enumerate(categories)}
 C=len(categories)
 matrix=[[0]*C for _ in range(C)]
 a_tot=[0]*C;b_tot=[0]*C;agreements=0
 for a,b in pairs:
  i=index[a];j=index[b];matrix[i][j]+=1;a_tot[i]+=1;b_tot[j]+=1
  if a==b:agreements+=1
 po=Fraction(agreements,n)
 pe=Fraction(sum(a_tot[j]*b_tot[j] for j in range(C)),n*n)
 if pe==1:
  raise UndefinedCohenKappa('Pe=1：两位标记者全部票落同一类别，κ未定义')
 kappa=(po-pe)/(1-pe)
 return {'kappa':float(kappa),'po':float(po),'pe':float(pe),'n':n,
  'confusion_matrix':matrix,'rater_a_totals':a_tot,'rater_b_totals':b_tot,'agreements':agreements}

def pair_bootstrap(pairs,categories,repeats,seed):
 # 每对按完整试样（两位共同有票的整行配对）有放回重采样；无法计算的重复保留并说明原因，不补抽
 n=len(pairs);rng=random.Random(seed);records=[];values=[];failures={}
 eligible_pool=n>=MIN_PAIR_SPECIMENS
 for i in range(repeats):
  indices=[rng.randrange(n) for _ in range(n)] if eligible_pool else []
  sample=[pairs[k] for k in indices]
  try:
   result=cohen_kappa(sample,categories);value=result['kappa'];values.append(value)
   records.append({'repeat':i,'sample_indices':indices,'kappa':value,'valid':True,'reason':None})
  except UndefinedCohenKappa as error:
   reason=str(error);failures[reason]=failures.get(reason,0)+1
   records.append({'repeat':i,'sample_indices':indices,'kappa':None,'valid':False,'reason':reason})
 valid=len(values)
 if not eligible_pool:
  interval=None;status='not_computable'
  interval_reason=f'共同有票试样不足{MIN_PAIR_SPECIMENS}个，未执行重采样，不报告经验区间'
 else:
  reportable=valid*10>=repeats*9
  interval=_percentile(values,[.025,.975]) if reportable else None
  status='reported' if reportable else 'insufficient_valid'
  interval_reason=('有效比例≥90%，有效重复的2.5%/97.5%线性percentile经验区间' if reportable else '有效重复少于90%，不报告经验区间')
 return {'seed':seed,'requested_repeats':repeats,'valid_repeats':valid,'invalid_repeats':repeats-valid,
  'valid_fraction':(valid/repeats) if repeats else 0.0,'invalid_reasons':failures,'interval':interval,
  'confidence_level':.95,'interval_status':status,'interval_reason':interval_reason,
  'quantile_method':'linear percentile (numpy.quantile method=linear equivalent)','replicates':records,
  'resampling_unit':'entire specimen pair row with replacement; only specimens both raters voted on',
  'resampling_pool_size':n}

def _percentile(values,qs):
 # 与 numpy.quantile(method='linear') 等价的线性分位数
 ordered=sorted(values);n=len(ordered)
 if n==0:return None
 out=[]
 for q in qs:
  pos=q*(n-1);lo=int(pos);frac=pos-lo
  if lo+1<n:out.append(ordered[lo]*(1-frac)+ordered[lo+1]*frac)
  else:out.append(float(ordered[lo]))
 return out

def pair_agreement(study,specimens,votes,repeats,seed):
 categories=study['categories'];raters=study['raters']
 ordered=sorted(specimens,key=lambda s:s['reference'])
 # specimen_id -> {rater: category}
 lookup={s['id']:{} for s in ordered}
 for vote in votes:
  lookup[vote['specimen_id']][vote['rater']]=vote['category']
 total=len(ordered);pairs=[]
 for rater_a,rater_b in combinations(raters,2):
  rows=[];included_refs=[];excluded=[]
  for specimen in ordered:
   labels=lookup[specimen['id']]
   if rater_a in labels and rater_b in labels:
    rows.append((labels[rater_a],labels[rater_b]));included_refs.append(specimen['reference'])
   else:
    missing=[r for r in (rater_a,rater_b) if r not in labels]
    excluded.append({'specimen_id':specimen['id'],'reference':specimen['reference'],'missing_raters':missing})
  n_common=len(rows)
  entry={'rater_a':rater_a,'rater_b':rater_b,'included_count':n_common,
   'excluded_count':total-n_common,'included_references':included_refs,
   'excluded_specimens':excluded,'categories':categories}
  try:
   stats=cohen_kappa(rows,categories)
   entry.update({'computable':True,'kappa':stats['kappa'],'observed_agreement':stats['po'],
    'chance_agreement':stats['pe'],'confusion_matrix':stats['confusion_matrix'],
    'rater_a_totals':stats['rater_a_totals'],'rater_b_totals':stats['rater_b_totals'],
    'agreements':stats['agreements'],'undefined_reason':None})
  except UndefinedCohenKappa as error:
   entry.update({'computable':False,'kappa':None,'observed_agreement':_fraction_or_none(
     Fraction(sum(1 for a,b in rows if a==b),n_common) if n_common else None),
    'chance_agreement':None,'confusion_matrix':None,'rater_a_totals':None,'rater_b_totals':None,
    'agreements':sum(1 for a,b in rows if a==b),'undefined_reason':str(error)})
  entry['bootstrap']=pair_bootstrap(rows,categories,repeats,seed)
  pairs.append(entry)
 return {'panel_specimen_count':total,'pairs':pairs,
  'interpretation':'每对标记者仅使用两人共同有票的完整试样；缺票不是类别，不计入混淆矩阵。重采样单位是共同有票的整试样配对，无法计算的重复保留原因且不补抽；区间受有效比例≥90%门槛限制。'}
