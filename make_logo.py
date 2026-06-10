import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import numpy as np

GOLD="#F0B90B"; BG="#0d0f12"; TXT="#e8eaed"; MUT="#7a828c"

def draw(ax, with_word=True, cx=50, cy=58, R=30):
    # the Band ring
    ax.add_patch(Circle((cx,cy),R,fill=False,ec=GOLD,lw=5.2,zorder=2))
    # four agent nodes on the ring (top, right, bottom, left)
    for ang in (90,0,270,180):
        a=np.radians(ang); nx,ny=cx+R*np.cos(a),cy+R*np.sin(a)
        ax.add_patch(Circle((nx,ny),4.6,fc=BG,ec=GOLD,lw=3.4,zorder=4))
        ax.add_patch(Circle((nx,ny),1.7,fc=GOLD,zorder=5))
    # inner calibration curve (S hugging the 45-degree diagonal)
    half=18.5
    x0,y0,x1,y1=cx-half,cy-half,cx+half,cy+half
    ax.plot([x0,x1],[y0,y1],ls=(0,(4,3)),color=MUT,lw=1.8,zorder=3)  # predicted=observed
    u=np.linspace(0,1,240)
    s=1/(1+np.exp(-7.4*(u-0.5)))
    ax.plot(x0+(x1-x0)*u, y0+(y1-y0)*s, color=GOLD, lw=3.6, solid_capstyle="round", zorder=3)
    if with_word:
        ax.text(cx,11,"BAND RISK-REVIEW",ha="center",va="center",color=TXT,
                fontsize=15,fontweight="bold")

# ---- lockup (icon + wordmark), dark bg ----
fig,ax=plt.subplots(figsize=(6,6),dpi=120); fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
ax.set_xlim(0,100); ax.set_ylim(0,100); ax.axis("off")
draw(ax,with_word=True)
plt.savefig("logo_band.png",facecolor=BG,bbox_inches="tight",pad_inches=0.25); plt.close()

# ---- icon only, transparent (for avatars/favicons) ----
fig,ax=plt.subplots(figsize=(6,6),dpi=120); ax.set_facecolor("none")
ax.set_xlim(0,100); ax.set_ylim(18,98); ax.axis("off")
draw(ax,with_word=False,cy=58)
plt.savefig("logo_band_icon.png",transparent=True,bbox_inches="tight",pad_inches=0.2); plt.close()
print("saved logo_band.png + logo_band_icon.png")
