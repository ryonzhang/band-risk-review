import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch
import numpy as np

GOLD="#F0B90B"; BG="#0d0f12"; PANEL="#14181d"; LINE="#2a313a"; TXT="#e8eaed"; MUT="#9aa3ad"

def ring_of_agents(ax, cx, cy, R, r, labels, lw=2.0, fs=9):
    pts=[]
    for i in range(4):
        a=np.pi/2 - i*np.pi/2          # top, right, bottom, left
        x,y=cx+R*np.cos(a), cy+R*np.sin(a)
        pts.append((x,y))
    # connecting band (arrows around the ring -> collaboration)
    for i in range(4):
        x1,y1=pts[i]; x2,y2=pts[(i+1)%4]
        ax.add_patch(FancyArrowPatch((x1,y1),(x2,y2),connectionstyle="arc3,rad=0.22",
                     arrowstyle="-|>",mutation_scale=11,color=GOLD,lw=lw,shrinkA=r*1.6,shrinkB=r*1.6,alpha=0.9))
    for (x,y),lab in zip(pts,labels):
        ax.add_patch(Circle((x,y),r,fc=PANEL,ec=GOLD,lw=lw))
        ax.text(x,y,lab,ha="center",va="center",color=GOLD,fontsize=fs,fontweight="bold")
    # center: calibration check
    ax.add_patch(Circle((cx,cy),r*0.62,fc=BG,ec=MUT,lw=lw*0.7))
    ax.text(cx,cy,"✓",ha="center",va="center",color=TXT,fontsize=fs*1.5,fontweight="bold")

# ---------- LOGO (square) ----------
fig,ax=plt.subplots(figsize=(6,6),dpi=110); fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
ax.set_xlim(0,100); ax.set_ylim(0,100); ax.axis("off")
ring_of_agents(ax,50,56,30,11,["D","R","C","Rv"],lw=2.6,fs=13)
ax.text(50,11,"BAND RISK-REVIEW",ha="center",color=TXT,fontsize=12.5,fontweight="bold")
plt.savefig("logo_band.png",facecolor=BG,bbox_inches="tight",pad_inches=0.3)
plt.close()

# ---------- COVER (1200x630 OG ratio) ----------
fig,ax=plt.subplots(figsize=(12,6.3),dpi=110); fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
ax.set_xlim(0,120); ax.set_ylim(0,63); ax.axis("off")
# subtle hairline frame
ax.add_patch(plt.Rectangle((1.2,1.2),117.6,60.6,fill=False,ec=LINE,lw=1.2))
# left: text
ax.text(7,49,"BAND RISK-REVIEW",color=GOLD,fontsize=30,fontweight="bold")
ax.text(7,41.5,"Four agents that collaborate through Band to make",color=TXT,fontsize=13)
ax.text(7,37,"high-stakes financial decisions — with calibration,",color=TXT,fontsize=13)
ax.text(7,32.5,"separation of duties, and an audit trail.",color=TXT,fontsize=13)
ax.text(7,22.5,"Data  →  Risk  →  Calibration  →  Reviewer",color=MUT,fontsize=12.5,style="italic")
ax.text(7,10,"Band of Agents Hackathon · Track 3 — Regulated & High-Stakes",color=MUT,fontsize=10.5)
ax.text(7,5.5,"CFA/ASA-built · MIT · github.com/ryonzhang/band-risk-review",color=MUT,fontsize=9.5)
# right: motif
ring_of_agents(ax,95,33,17,6.4,["D","R","C","Rv"],lw=2.2,fs=10)
plt.savefig("cover_band.png",facecolor=BG,bbox_inches="tight",pad_inches=0.0)
print("saved logo_band.png + cover_band.png")
