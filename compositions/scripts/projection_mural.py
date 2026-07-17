"""Projection screen: mini recursive scene with a real Voronoi diagram
(moving seed points, brute-force nearest-neighbor per pixel cell)."""

import argparse
import json
import sys
import urllib.request

import os
BASE = f"http://localhost:{os.environ.get('LIVECODE_PORT', '8766')}"

_parser = argparse.ArgumentParser()
_parser.add_argument("--dump-steps", action="store_true",
                     help="Print commands as JSON steps to stdout instead of executing")
_args = _parser.parse_args()
_collected: list[dict] = []


def post(path, payload):
    if _args.dump_steps:
        _collected.append({"route": path, "payload": dict(payload)})
        return {"ok": True}
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{BASE}{path}", data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


BUILDING = """
push();
noStroke();

// ── geometry ──────────────────────────────────────────────────
const bx = width * 0.06;
const bw = width * 0.88;
const bottomY = height * 0.78;
const topY = height * 0.30;
const peakX = bx + bw * 0.62;
const peakY = height * 0.235;
const rightX = bx + bw;
const rightTopY = height * 0.55;

function roofY(x) {
  if (x <= peakX) {
    const t = (x - bx) / (peakX - bx);
    return lerp(topY, peakY, t);
  } else {
    const t = (x - peakX) / (rightX - peakX);
    return lerp(peakY, rightTopY, t);
  }
}

fill(22, 18, 20);
beginShape();
for (let x = bx; x <= rightX; x += 6) vertex(x, roofY(x));
vertex(rightX, bottomY);
vertex(bx, bottomY);
endShape(CLOSE);

const palette = [
  [30,32,56],[25,22,70],[35,14,82],[40,28,88],
  [10,68,60],[15,75,75],[350,55,50],[355,70,45],
  [280,32,48],[255,28,42],[0,0,92],[42,32,92],
  [120,28,42],[95,35,50],[25,48,32],[20,38,28],
  [0,0,28],[35,18,24],
];
function hash2(i,j){let h=(i*374761393+j*668265263)|0;h=(h^(h>>>13))*1274126177|0;return(h^(h>>>16))>>>0;}

const cols=16, rows=6;
const cellW=bw/cols, cellH=(bottomY-topY)/rows;

for(let i=0;i<cols;i++){
  for(let j=0;j<rows;j++){
    const px=bx+i*cellW, py=topY+j*cellH;
    const cx=px+cellW*0.5, top=roofY(cx);
    if(py+cellH<top) continue;
    const drawTop=max(py,top), hh=(py+cellH)-drawTop;
    if(hh<4) continue;
    const hk=hash2(i,j), c=palette[hk%palette.length];
    const inset=((hk>>4)&3)*0.5, ww=cellW-inset*2;
    fill(c[0],c[1],c[2]);
    rect(px+inset,drawTop,ww,hh-inset);
    if(c[0]>=25&&c[0]<=45&&(hk&7)<3){
      stroke(c[0],c[1]+10,c[2]-18,55); strokeWeight(0.5);
      for(let g=0;g<3;g++){const gy=drawTop+(g+1)*(hh/4);line(px+inset+4,gy,px+ww-4,gy);}
      noStroke();
    }
  }
}

// pixel panel, door, red triangle (unchanged)
const pbx=bx+bw*0.58, pby=topY+cellH*0.55, pbw=cellW*1.1, pbh=cellH*1.4;
for(let py=0;py<8;py++) for(let px2=0;px2<6;px2++){
  fill(0,0,((px2*13+py*7+(px2^py))&1)?96:6);
  rect(pbx+px2*pbw/6,pby+py*pbh/8,pbw/6+1,pbh/8+1);
}
fill(48,78,92);
const doorX=bx+bw*0.51, doorY=topY+cellH*0.55;
rect(doorX,doorY,cellW*0.6,cellH*1.4);
fill(45,90,70); rect(doorX+3,doorY+3,cellW*0.6-6,cellH*1.4-6);
fill(8,78,65);
beginShape();
vertex(bx+bw*0.78,roofY(bx+bw*0.78)); vertex(rightX,rightTopY);
vertex(rightX,rightTopY+cellH*1.2); vertex(bx+bw*0.78,roofY(bx+bw*0.78)+cellH*1.6);
endShape(CLOSE);

// ── PROJECTION SCREEN ─────────────────────────────────────────
const sx=bx+bw*0.04, sy=topY+(bottomY-topY)*0.10;
const sw=bw*0.55, sh=(bottomY-topY)*0.75;

push(); blendMode(ADD);
for(let r=24;r>0;r-=3){fill(220,30,90,pow(r/24,1.4)*7);rect(sx-r,sy-r,sw+r*2,sh+r*2,6);}
blendMode(BLEND); pop();
fill(0,0,6); rect(sx-5,sy-5,sw+10,sh+10);

push();
drawingContext.save();
drawingContext.beginPath();
drawingContext.rect(sx,sy,sw,sh);
drawingContext.clip();
drawMiniScene(sx,sy,sw,sh);
drawingContext.restore();
pop();

stroke(0,0,0,12); strokeWeight(1);
for(let yy=sy;yy<sy+sh;yy+=3) line(sx,yy,sx+sw,yy);
noStroke();

// ── BIG ROTATING MANDALA ──────────────────────────────────────
const mx=bx+bw*0.79, my=topY+cellH*2.0, mmr=cellH*1.5;
push(); translate(mx,my);
blendMode(ADD);
for(let r=6;r>0;r--){fill(20,70,90,8);circle(0,0,mmr*2.2+r*8);}
blendMode(BLEND);
push(); rotate(frameCount*0.005); noFill();
stroke(195,65,78); strokeWeight(3);
for(let k=0;k<8;k++){push();rotate(k*TAU/8);ellipse(0,mmr*0.55,mmr*0.50,mmr*1.05);pop();}
stroke(45,80,92); strokeWeight(2);
for(let k=0;k<8;k++){push();rotate(k*TAU/8+PI/8);ellipse(0,mmr*0.32,mmr*0.22,mmr*0.6);pop();}
pop();
push(); rotate(-frameCount*0.008);
stroke(15,75,80); strokeWeight(1.6);
for(let k=0;k<12;k++){push();rotate(k*TAU/12);line(0,mmr*0.10,0,mmr*0.42);pop();}
pop();
noStroke();
fill(48,75,92); circle(0,0,mmr*0.55);
fill(15,80,80); circle(0,0,mmr*0.34);
fill(280,40,65); circle(0,0,mmr*0.18);
fill(0,0,96); circle(0,0,mmr*0.08);
pop();

pop();

// ============================================================
// HELPERS
// ============================================================

function drawMiniScene(x,y,w,h){
  const horizonY=h*0.78;
  for(let yy=0;yy<horizonY;yy+=2){
    const t=yy/horizonY;
    fill(lerp(208,35,pow(t,1.4)),lerp(40,14,t),lerp(82,96,t));
    rect(x,y+yy,w,3);
  }
  noStroke();
  for(let i=0;i<4;i++){
    fill(35,8,100,35);
    ellipse(x+(((i*0.23+frameCount*0.0007)%1.2)-0.1)*w, y+h*(0.07+i*0.045), w*0.18, h*0.012);
  }
  for(let yy=horizonY;yy<h;yy++){
    const t=(yy-horizonY)/(h-horizonY);
    fill(28,lerp(18,28,t),lerp(88,70,t));
    rect(x,y+yy,w,2);
  }
  const mbx=x+w*0.06, mbw=w*0.88;
  const mbottomY=y+h*0.78, mtopY=y+h*0.30;
  fill(22,18,20); rect(mbx,mtopY,mbw,mbottomY-mtopY);
  const mp=[[30,32,56],[25,22,70],[35,14,82],[10,68,60],[350,55,50],[280,32,48],[0,0,92],[120,28,42],[25,48,32],[0,0,28]];
  const mc=12, mr2=5, mcw=mbw/mc, mch=(mbottomY-mtopY)/mr2;
  for(let i=0;i<mc;i++) for(let j=0;j<mr2;j++){
    const hk=((i*374761393+j*668265263)|0)>>>0;
    const c=mp[hk%mp.length]; fill(c[0],c[1],c[2]);
    rect(mbx+i*mcw,mtopY+j*mch,mcw-0.4,mch-0.4);
  }
  fill(48,78,92); rect(mbx+mbw*0.51,mtopY+mch*0.55,mcw*0.6,mch*1.4);

  // inner screen with REAL VORONOI
  const isx=mbx+mbw*0.04, isy=mtopY+(mbottomY-mtopY)*0.10;
  const isw=mbw*0.55, ish=(mbottomY-mtopY)*0.75;
  fill(0,0,6); rect(isx-2,isy-2,isw+4,ish+4);
  push();
  drawingContext.save();
  drawingContext.beginPath();
  drawingContext.rect(isx,isy,isw,ish);
  drawingContext.clip();
  drawVoronoi(isx,isy,isw,ish);
  drawingContext.restore();
  pop();

  drawMiniFire(x+w*0.50, y+h*0.905);
  drawMiniRiders(x+w*0.50, y+h*0.905, w*0.22, h*0.06);
}

function drawVoronoi(x,y,w,h){
  // 14 seed points drifting on unique noise orbits
  const N = 14;
  const seeds = [];
  for(let i=0;i<N;i++){
    const sx = x + noise(i*1.7, frameCount*0.004) * w;
    const sy = y + noise(i*1.7+100, frameCount*0.004) * h;
    const hue = (i * 360/N + frameCount*0.8) % 360;
    seeds.push({x:sx, y:sy, hue});
  }

  // brute-force voronoi via pixel-buffer on an offscreen graphics
  // too slow per-pixel — use coarse grid cells instead
  const step = 6;
  const cw = ceil(w/step), ch = ceil(h/step);
  noStroke();
  for(let ci=0;ci<cw;ci++){
    for(let cj=0;cj<ch;cj++){
      const px = x + ci*step + step*0.5;
      const py = y + cj*step + step*0.5;
      let minD = 1e9, nearest = 0;
      for(let k=0;k<N;k++){
        const dx = px-seeds[k].x, dy = py-seeds[k].y;
        const d = dx*dx+dy*dy;
        if(d<minD){minD=d; nearest=k;}
      }
      const s = seeds[nearest];
      fill(s.hue, 65, 90);
      rect(x+ci*step, y+cj*step, step, step);
    }
  }

  // cell edges: draw again checking 2nd-nearest, mark boundary cells
  stroke(0,0,20);
  strokeWeight(1.2);
  for(let ci=0;ci<cw;ci++){
    for(let cj=0;cj<ch;cj++){
      const px = x+ci*step+step*0.5, py = y+cj*step+step*0.5;
      let d1=1e9, d2=1e9, n1=0;
      for(let k=0;k<N;k++){
        const dx=px-seeds[k].x, dy=py-seeds[k].y, d=dx*dx+dy*dy;
        if(d<d1){d2=d1; d1=d; n1=k;}
        else if(d<d2){d2=d;}
      }
      const ratio = sqrt(d1)/(sqrt(d2)+0.001);
      if(ratio > 0.85){
        point(x+ci*step+step*0.5, y+cj*step+step*0.5);
      }
    }
  }
  noStroke();

  // seed dots (red with dark outline, like the reference image)
  for(let i=0;i<N;i++){
    fill(0,0,15); circle(seeds[i].x, seeds[i].y, 7);
    fill(0,90,75); circle(seeds[i].x, seeds[i].y, 5);
  }
}

function drawMiniFire(fx,fy){
  push(); translate(fx,fy); noStroke();
  push(); blendMode(ADD);
  for(let r=26;r>0;r-=3){fill(22,75,95,9);circle(0,-3,r*2);}
  blendMode(BLEND); pop();
  fill(15,90,70,90); ellipse(0,0,16,4);
  for(let i=0;i<9;i++){
    const t=frameCount*0.10+i*1.41;
    const xJ=(noise(i*0.6,t*0.07)-0.5)*12;
    const fh=8+noise(i+30,t*0.10)*18;
    const fw=4+noise(i+80,t*0.09)*4;
    fill(lerp(48,4,noise(i+30,t*0.10)),90,100,65);
    triangle(xJ-fw/2,0,xJ+fw/2,0,xJ+fw*0.15,-fh);
  }
  pop();
}

function drawMiniRiders(fx,fy,rx,ry){
  const ride=frameCount*0.013;
  const pals=[
    {shirt:[200,80,75],helmet:[10,90,80]},
    {shirt:[55,85,90],helmet:[125,70,55]},
    {shirt:[285,55,78],helmet:[200,80,72]},
    {shirt:[120,55,60],helmet:[42,90,92]},
    {shirt:[348,75,82],helmet:[280,65,75]},
  ];
  const placed=[];
  for(let i=0;i<5;i++){
    const angle=ride+i*TAU/5;
    const px=fx+cos(angle)*rx, py=fy+sin(angle)*ry;
    const depth=sin(angle);
    const sc=lerp(0.32,0.6,(depth+1)/2);
    placed.push({x:px,y:py,sc,depth,P:pals[i]});
  }
  placed.sort((a,b)=>a.depth-b.depth);
  for(const r of placed){
    push(); translate(r.x,r.y); noStroke();
    fill(0,0,0,35); ellipse(0,1,18*r.sc,4*r.sc);
    fill(0,0,8); ellipse(0,-7*r.sc,12*r.sc,11*r.sc);
    fill(0,0,10); rect(-4*r.sc,-16*r.sc,8*r.sc,10*r.sc,1);
    fill(16,75,80); rect(-4*r.sc,-17*r.sc,8*r.sc,2*r.sc);
    fill(r.P.shirt[0],r.P.shirt[1],r.P.shirt[2]);
    ellipse(0,-22*r.sc,9*r.sc,12*r.sc);
    fill(r.P.helmet[0],r.P.helmet[1],r.P.helmet[2]);
    circle(0,-30*r.sc,8*r.sc);
    pop();
  }
}
"""


def main():
    post("/p5/layer", {"name": "building", "code": BUILDING})

    if _args.dump_steps:
        json.dump(_collected, sys.stdout)
    else:
        print("Voronoi live.")


if __name__ == "__main__":
    main()
