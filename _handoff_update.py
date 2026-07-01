
content = open(r'C:ig_engine\HANDOFF.md','r',encoding='utf-8').read()
content = content.replace('**Last updated:** 2026-07-01 15:18 (UTC)','**Last updated:** 2026-07-01 15:18 (UTC)',1)
entry = '- [15:18Z 07-01] routine fire headless (claude -p): MISSED_FIRES=0, 1 iter. Divergence: 1030watched/4in/4out/41open/3379hist (FOR,HCSG,MTH,TMHC; EXAS/HOLX 404; MCW/VRRM err); TRB-50: 1115watched/0in/0out/78open; queue EMPTY; dashboard 1.83MB; commit efb00dc PUSHED. Sentinel 15:18Z. SKILL.md via _skill_content.txt.
'
if entry not in content:
    content = content.replace('## Last actions
','## Last actions
'+entry,1)
open(r'C:ig_engine\HANDOFF.md','w',encoding='utf-8').write(content)
print('done')
