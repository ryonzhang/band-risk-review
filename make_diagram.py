import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

GOLD="#F0B90B"; BG="#0d0f12"; PANEL="#14181d"; LINE="#2a313a"; TXT="#e8eaed"; MUT="#9aa3ad"; DIM="#3a4350"
fig,ax=plt.subplots(figsize=(12.8,6.4),dpi=170); fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
ax.set_xlim(0,128); ax.set_ylim(0,64); ax.axis("off")

def box(x,y,w,h,title,sub,edge=LINE,tc=TXT,ts=10.5,ss=7.2):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.5,rounding_size=1.8",fc=PANEL,ec=edge,lw=1.8))
    ax.text(x+w/2,y+h*0.60,title,ha="center",va="center",color=tc,fontsize=ts,fontweight="bold")
    ax.text(x+w/2,y+h*0.26,sub,ha="center",va="center",color=MUT,fontsize=ss)

def arrow(x1,y1,x2,y2,c=GOLD,lw=1.9):
    ax.add_patch(FancyArrowPatch((x1,y1),(x2,y2),arrowstyle="-|>",mutation_scale=14,color=c,lw=lw,shrinkA=2,shrinkB=2))

def label(x,y,t,c=MUT,fs=7.6):
    ax.text(x,y,t,ha="center",va="center",color=c,fontsize=fs,style="italic")

ax.text(60,60,"Band Risk-Review  —  agents collaborating through Band",ha="center",color=GOLD,fontsize=14,fontweight="bold")
ax.text(60,55,"Track 3 · Regulated & High-Stakes financial workflows",ha="center",color=MUT,fontsize=9)

# Band room
ax.add_patch(FancyBboxPatch((23,7),99,40,boxstyle="round,pad=0.5,rounding_size=2",fc="#101418",ec=GOLD,lw=1.4,ls=(0,(5,3))))
ax.text(72,43.4,"BAND ROOM   ·   shared, auditable message bus",ha="center",color=GOLD,fontsize=9,fontweight="bold")

# User (outside)
box(1,28,19,12,"User / Advisor","“Add to BTC?”",edge=GOLD,ts=10)

# pipeline (single row) — matches turn order
yA=28; h=12; ycen=yA+h/2
box(25,yA,20,h,"1 · Data","MongoDB MCP",ts=10,ss=7)
box(48,yA,20,h,"2 · Risk","shares · HHI · DD",ts=10,ss=7)
box(71,yA,20,h,"3 · Calibration","prob · conf · Kelly",ts=10,ss=7)
box(94,yA,20,h,"4 · Reviewer","approve / ESCALATE",edge=GOLD,tc=GOLD,ts=10,ss=6.8)

arrow(20,ycen,25,ycen);  label(22.5,ycen+3,"request")
arrow(45,ycen,48,ycen);  label(46.5,ycen+3.2,"evidence")
arrow(68,ycen,71,ycen);  label(69.5,ycen+3.2,"risk")
arrow(91,ycen,94,ycen);  label(92.5,ycen+3.8,"sized rec")

# deterministic core + dotted "calls" (kept clear of the return path)
box(30,11,70,8,"risk_core — deterministic","Brier/ECE · fractional Kelly · HHI · drawdown   (LLM narrates, never invents)",edge=DIM,ts=9.5,ss=6.8)
for cx in (35,58,81,98):
    arrow(cx,yA,cx,19,c=DIM,lw=1.2)
label(72,9.0,"all four agents call the deterministic core",c=MUT,fs=6.8)

# Reviewer -> User : ONE continuous path routed around the right + bottom, arrowhead at end
px=[114,124,124,10.5,10.5]; py=[ycen,ycen,3,3,27.4]
ax.plot(px,py,color=GOLD,lw=2.0,solid_capstyle="round",solid_joinstyle="round")
ax.plot([10.5],[28],marker="^",color=GOLD,markersize=11)   # arrowhead into User
label(64,1.3,"verdict + audit trail   ·   answer or escalation",c=GOLD,fs=7.8)

plt.savefig("architecture_band.png",facecolor=BG,bbox_inches="tight",pad_inches=0.2)
print("saved")
