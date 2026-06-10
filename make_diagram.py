import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

GOLD="#F0B90B"; BG="#0d0f12"; PANEL="#14181d"; LINE="#2a313a"; TXT="#e8eaed"; MUT="#9aa3ad"
fig,ax=plt.subplots(figsize=(11,6.4),dpi=170); fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
ax.set_xlim(0,100); ax.set_ylim(0,100); ax.axis("off")

def box(x,y,w,h,title,sub,edge=LINE,tc=TXT):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.6,rounding_size=2.2",
                 fc=PANEL,ec=edge,lw=1.8))
    ax.text(x+w/2,y+h*0.62,title,ha="center",va="center",color=tc,fontsize=11,fontweight="bold")
    ax.text(x+w/2,y+h*0.27,sub,ha="center",va="center",color=MUT,fontsize=7.8)

def arrow(x1,y1,x2,y2,label="",c=GOLD,rad=0.0,off=2.2):
    ax.add_patch(FancyArrowPatch((x1,y1),(x2,y2),connectionstyle=f"arc3,rad={rad}",
                 arrowstyle="-|>",mutation_scale=15,color=c,lw=1.7,shrinkA=3,shrinkB=3))
    if label:
        ax.text((x1+x2)/2,(y1+y2)/2+off,label,ha="center",va="center",color=MUT,fontsize=7.2,
                style="italic")

ax.text(50,95,"Band Risk-Review  —  multi-agent collaboration through Band",
        ha="center",color=GOLD,fontsize=14,fontweight="bold")
ax.text(50,89.5,"Track 3 · Regulated & High-Stakes financial workflows",ha="center",color=MUT,fontsize=9)

# User
box(4,70,20,12,"User / Advisor","“Should I add to BTC?”",edge=GOLD)
# Band room band (the collaboration substrate)
ax.add_patch(FancyBboxPatch((30,8),66,72,boxstyle="round,pad=0.6,rounding_size=2.2",
             fc="#101418",ec=GOLD,lw=1.4,ls=(0,(5,3))))
ax.text(63,76.5,"BAND ROOM  (shared, auditable message bus)",ha="center",color=GOLD,fontsize=9.5,fontweight="bold")

# 4 agents
box(34,55,26,12,"1 · Data Agent","MongoDB Atlas MCP → evidence packet")
box(66,55,26,12,"2 · Risk Agent","risk shares · HHI · drawdown est.")
box(34,30,26,12,"3 · Calibration Agent","calibrated prob · confidence · Kelly size")
box(66,30,26,12,"4 · Reviewer Agent","policy gate · approve / trim / ESCALATE",edge=GOLD,tc=GOLD)

# deterministic core
box(46,11,34,11,"risk_core  (deterministic)","Brier/ECE · fractional Kelly · HHI · DD — LLM never invents numbers",edge="#3a4350")

# flows
arrow(24,76,40,67,"request",rad=-0.15)
arrow(47,55,47,42,"evidence",rad=0.0)        # data -> calibration (down)
arrow(60,61,66,61,"evidence",rad=0.0)        # data -> risk
arrow(79,55,79,42,"risk metrics",rad=0.0)    # risk -> reviewer (down)
arrow(60,36,66,36,"sized rec",rad=0.0)       # calibration -> reviewer
arrow(63,30,63,22,"calls",c="#3a4350",rad=0.0)   # agents -> core
arrow(79,30,40,15,"verdict + audit trail",c=GOLD,rad=0.2)
arrow(34,36,24,72,"answer / escalation",c=GOLD,rad=0.3)

plt.savefig("architecture_band.png",facecolor=BG,bbox_inches="tight",pad_inches=0.25)
print("saved architecture_band.png")
