#!/usr/bin/env python3
"""Capability probe for the generative factory. Deploys representative heavy
p5-2D techniques to the live canvas, measures fps, writes PROBE.md."""
import time, requests, statistics, sys
BASE = "http://localhost:8766"

def post(p, b): return requests.post(BASE+p, json=b, timeout=15).json()
def read(k):
    d = requests.get(BASE+f"/p5/read?key={k}", timeout=10).json()
    return d.get("value")

def fps_of(name, code, warm=3.5, samples=6):
    post("/p5/layer", {"name": name, "code": code})
    time.sleep(warm)
    vals = []
    for _ in range(samples):
        v = read("clk")
        if v: vals.append(v.get("fps", 0))
        time.sleep(0.4)
    post("/p5/remove", {"name": name})
    post("/p5/state", {"key": name, "value": None})
    time.sleep(0.6)
    return statistics.median(vals) if vals else 0

PROBES = {
"baseline_fill": "background(230,40,10);",

"pix_128x72": """if(!window.state._p||window.state._p.width!=128){window.state._p=createGraphics(128,72);}
var g=window.state._p; g.loadPixels(); var t=window.state.clk.t; var px=g.pixels;
for(var y=0;y<72;y++)for(var x=0;x<128;x++){var i=4*(y*128+x); var v=128+127*Math.sin(x*0.1+t)*Math.cos(y*0.13+t*0.7); px[i]=v;px[i+1]=v*0.6;px[i+2]=200-v*0.5;px[i+3]=255;}
g.updatePixels(); image(g,0,0,width,height);""",

"pix_192x108": """if(!window.state._p||window.state._p.width!=192){window.state._p=createGraphics(192,108);}
var g=window.state._p; g.loadPixels(); var t=window.state.clk.t; var px=g.pixels;
for(var y=0;y<108;y++)for(var x=0;x<192;x++){var i=4*(y*192+x); var v=128+127*Math.sin(x*0.08+t)*Math.cos(y*0.1+t*0.7); px[i]=v;px[i+1]=v*0.6;px[i+2]=200-v*0.5;px[i+3]=255;}
g.updatePixels(); image(g,0,0,width,height);""",

"pix_256x256": """if(!window.state._p||window.state._p.width!=256){window.state._p=createGraphics(256,256);}
var g=window.state._p; g.loadPixels(); var t=window.state.clk.t; var px=g.pixels;
for(var y=0;y<256;y++)for(var x=0;x<256;x++){var i=4*(y*256+x); var v=128+127*Math.sin(x*0.06+t)*Math.cos(y*0.07+t*0.7); px[i]=v;px[i+1]=v*0.6;px[i+2]=200-v*0.5;px[i+3]=255;}
g.updatePixels(); image(g,0,0,width,height);""",

"domainwarp_128x72_3oct": """if(!window.state._p||window.state._p.width!=128){window.state._p=createGraphics(128,72);}
var g=window.state._p; g.loadPixels(); var t=window.state.clk.t; var px=g.pixels;
function n(x,y){return (Math.sin(x*1.7+y*0.3)+Math.sin(y*1.3-x*0.4)+Math.sin((x+y)*0.9))/3;}
for(var y=0;y<72;y++)for(var x=0;x<128;x++){var i=4*(y*128+x);var fx=x*0.05,fy=y*0.05;
var q=n(fx+t*0.1,fy)+0.5*n(fx*2,fy*2+t*0.05)+0.25*n(fx*4+t*0.02,fy*4);
var v=128+127*Math.sin(q*3.0+t); px[i]=v;px[i+1]=80+v*0.4;px[i+2]=200-v*0.5;px[i+3]=255;}
g.updatePixels(); image(g,0,0,width,height);""",

"points_500": """background(230,40,8); stroke(200,80,90); strokeWeight(2); var t=window.state.clk.t;
beginShape(POINTS); for(var i=0;i<500;i++){var a=i*0.3+t; vertex(width/2+Math.cos(a)*i*0.4, height/2+Math.sin(a*1.1)*i*0.4);} endShape();""",

"points_2000": """background(230,40,8); stroke(200,80,90); strokeWeight(1.5); var t=window.state.clk.t;
beginShape(POINTS); for(var i=0;i<2000;i++){var a=i*0.1+t; vertex(width/2+Math.cos(a)*i*0.12, height/2+Math.sin(a*1.1)*i*0.12);} endShape();""",

"heavy_150_add": """background(230,40,8); blendMode(ADD); noStroke(); var t=window.state.clk.t;
for(var i=0;i<150;i++){var a=i*0.4+t; fill((i*7)%360,70,90,25); ellipse(width/2+Math.cos(a)*250, height/2+Math.sin(a*1.2)*200, 120,120);} blendMode(BLEND);""",

"feedback_fullcanvas": """if(!window.state._fb||window.state._fbw!=width){window.state._fb=createGraphics(Math.floor(width/2),Math.floor(height/2));window.state._fbw=width;}
var g=window.state._fb; var t=window.state.clk.t;
g.push(); g.translate(g.width/2,g.height/2); g.scale(1.01); g.rotate(0.003); g.translate(-g.width/2,-g.height/2);
g.image(g,0,0); g.pop(); g.noStroke(); g.fill((t*20)%360,80,90,40); g.ellipse(g.width/2+Math.cos(t)*60,g.height/2+Math.sin(t*1.3)*40,30,30);
image(g,0,0,width,height);""",

"shadowblur_24": """background(230,40,8); var t=window.state.clk.t; drawingContext.shadowBlur=30; noStroke();
for(var i=0;i<24;i++){var a=i*0.5+t; drawingContext.shadowColor='hsl('+((i*15)%360)+',80%,60%)'; fill((i*15)%360,80,95); ellipse(width/2+Math.cos(a)*220,height/2+Math.sin(a*1.1)*180,40,40);} drawingContext.shadowBlur=0;""",

"marching_96x54": """if(!window.state._mg){window.state._mg=1;} background(220,50,10); var t=window.state.clk.t;
stroke(180,70,90); strokeWeight(1.5); noFill(); var GW=96,GH=54, cw=width/GW, ch=height/GH;
function f(x,y){return Math.sin(x*0.2+t)+Math.cos(y*0.2-t*0.7)+Math.sin((x+y)*0.1+t*0.3);}
for(var y=0;y<GH;y++)for(var x=0;x<GW;x++){var v=f(x,y); if(v>0&&v<0.3){point(x*cw,y*ch);}}""",
}

lines = ["# PROBE.md — live capability measurements (generative factory)", ""]
lines.append(f"_Measured {time.strftime('%Y-%m-%d %H:%M')} on the live 8766 canvas (idle baseline)._\n")
lines.append("| probe | median fps | verdict |")
lines.append("|---|---|---|")
results = {}
for name, code in PROBES.items():
    f = fps_of(name, code)
    results[name] = f
    verdict = "OK (≥50)" if f>=50 else ("marginal (25-50)" if f>=25 else "TOO SLOW (<25)")
    lines.append(f"| {name} | {f:.1f} | {verdict} |")
    print(f"{name:28s} {f:6.1f} fps  {verdict}", flush=True)

open("research/generative/PROBE.md","w").write("\n".join(lines)+"\n")
print("\nwrote research/generative/PROBE.md")
