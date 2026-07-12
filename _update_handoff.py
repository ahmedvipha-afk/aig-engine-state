with open("HANDOFF.md","r",encoding="utf-8") as fh:
    c=fh.read()
e="- [01:20Z 07-12] routine fire headless (claude -p): MISSED_FIRES=0, 1 iter. Divergence: 1030watched/4in/4out/41open/5078hist (FOR,HCSG,MTH,TMHC; EXAS/HOLX 404; MCW/VRRM err); TRB-50: 1115watched/0in/0out/78open; queue EMPTY; dashboard 2.51MB; commit 4411ced PUSH_VERIFIED. Sentinel 01:20Z. SKILL.md via _skill_content.txt. All steps fg.
"
c=c.replace("## Last actions
","## Last actions
"+e,1)
with open("HANDOFF.md","w",encoding="utf-8") as fh:
    fh.write(c)
print("HANDOFF updated")
