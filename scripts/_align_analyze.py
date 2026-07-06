"""Objective alignment check between EEVEE seg silhouette and Cycles beauty
silhouette. Both rendered from the SAME camera with a flat emission override,
so any difference is pure camera projection (not shading/bloom/exposure)."""
from PIL import Image
import numpy as np
import os

d = r"C:\Users\NVIDIA\Documents\Computex\_align_test"


def load_mask(f):
    im = np.array(Image.open(os.path.join(d, f)).convert("RGBA"))
    return im[..., 3] > 128


def bbox(m):
    ys, xs = np.where(m)
    return dict(xmin=int(xs.min()), ymin=int(ys.min()),
               xmax=int(xs.max()), ymax=int(ys.max()), count=int(m.sum()))


def centroid(m):
    ys, xs = np.where(m)
    return (round(float(xs.mean()), 1), round(float(ys.mean()), 1))


me = load_mask("sil_eevee.png")
mc = load_mask("sil_cycles.png")
print("resolution:", me.shape)
be, bc = bbox(me), bbox(mc)
print("EEVEE  bbox:", be)
print("CYCLES bbox:", bc)
print("edge deltas (cyc-eevee)  xmin %+d  ymin %+d  xmax %+d  ymax %+d" % (
    bc["xmin"] - be["xmin"], bc["ymin"] - be["ymin"],
    bc["xmax"] - be["xmax"], bc["ymax"] - be["ymax"]))
ce, cc = centroid(me), centroid(mc)
print("EEVEE centroid:", ce, " CYCLES centroid:", cc)
print("centroid delta:  dx %+.1f  dy %+.1f" % (cc[0] - ce[0], cc[1] - ce[1]))
inter = int((me & mc).sum())
union = int((me | mc).sum())
print("IoU (overlap):", round(inter / union, 4))
print("verdict:", "ALIGNED (illusion)" if inter / union > 0.985 else "REAL OFFSET")
