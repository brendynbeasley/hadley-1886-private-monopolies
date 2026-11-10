"""Draw the figures as SVG.

build() returns inline SVG (styled by the report's CSS variables) for
src/build_report.py. Running this file writes standalone copies, with
fixed light-theme colors, to figures/.
"""
import pandas as pd

from common import fred
from config import FIGURES, PROCESSED

COL={'Rail':'var(--s1)','Truck':'var(--s2)','Air':'var(--s3)'}
def strip(var,lo,hi,ticks,unit,aria):
    W,H,L,R,T=360,190,54,44,14; rows={'Rail':T+22,'Truck':T+72,'Air':T+122}; base=T+150
    x=lambda v:L+(v-lo)/(hi-lo)*(W-L-R)
    o=[f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{aria}" class="chart">']
    for t in ticks:
        o.append(f'<line x1="{x(t):.1f}" y1="{T}" x2="{x(t):.1f}" y2="{base}" class="grid"/><text x="{x(t):.1f}" y="{base+16}" class="tick" text-anchor="middle">{t}{unit}</text>')
    o.append(f'<line x1="{L}" y1="{base}" x2="{W-R}" y2="{base}" class="axis"/>')
    for m,y in rows.items():
        g=fm[fm['mode']==m]; mu=g[var].mean()
        o.append(f'<text x="{L-10}" y="{y+4}" class="lab" text-anchor="end">{m}</text>')
        o.append(f'<line x1="{x(mu):.1f}" y1="{y-13}" x2="{x(mu):.1f}" y2="{y+13}" class="mean"/>')
        for i,(_,r) in enumerate(g.sort_values(var).iterrows()):
            yy=y+(-5 if i%2 else 5)
            o.append(f'<circle cx="{x(r[var]):.1f}" cy="{yy}" r="5" fill="{COL[m]}" class="dot"><title>{r.firm}: {r[var]:.1f}%</title></circle>')
        o.append(f'<text x="{W-R+6}" y="{y+4}" class="val">{mu:.1f}%</text>')
    o.append('</svg>'); return '\n'.join(o)
def line(series,x0,x1,lo,hi,yt,xt,W=720,H=320,R=96,extra=lambda x,y:'',labels=None):
    L,T,B=40,16,30; x=lambda v:L+(v-x0)/(x1-x0)*(W-L-R); y=lambda v:T+(hi-v)/(hi-lo)*(H-T-B)
    o=[]
    for t in yt: o.append(f'<line x1="{L}" y1="{y(t):.1f}" x2="{W-R}" y2="{y(t):.1f}" class="grid"/><text x="{L-6}" y="{y(t)+4:.1f}" class="tick" text-anchor="end">{t}</text>')
    for t in xt: o.append(f'<text x="{x(t):.1f}" y="{H-B+18}" class="tick" text-anchor="middle">{t}</text>')
    o.append(f'<line x1="{L}" y1="{H-B}" x2="{W-R}" y2="{H-B}" class="axis"/>')
    o.append(extra(x,y))
    for name,s,col,cls,dy in series:
        s=s.dropna(); pts=' '.join(f'{x(k):.1f},{y(v):.1f}' for k,v in s.items())
        o.append(f'<polyline points="{pts}" fill="none" stroke="{col}" class="{cls}"/>')
        for k,v in s.items(): o.append(f'<circle cx="{x(k):.1f}" cy="{y(v):.1f}" r="7" fill="transparent" stroke="none"><title>{name}, {k}: {v:.1f}</title></circle>')
        k,v=s.index[-1],s.iloc[-1]
        o.append(f'<circle cx="{x(k):.1f}" cy="{y(v):.1f}" r="4" fill="{col}" class="dot"/>')
        if labels: o.append(f'<text x="{x(k)+9:.1f}" y="{y(v)+4+dy:.1f}" class="lab">{name} <tspan class="val">{v:.0f}</tspan></text>')
    return o,x,y,W,H

def build():
    global fm
    fm = pd.read_csv(PROCESSED / "firm_means.csv")
    pr = pd.read_csv(PROCESSED / "prices_annual.csv", index_col=0)
    # real rail
    rr=pr.real_rail
    def ex(x,y):
        s=f'<line x1="{x(1980):.1f}" y1="{y(110):.1f}" x2="{x(1980):.1f}" y2="{y(60):.1f}" class="ann"/><text x="{x(1980)+6:.1f}" y="{y(60)-8:.1f}" class="tick">Staggers Act, 1980</text>'
        for yr,dx,dy,a,t in [(1981,-8,-8,'end','1981: 104'),(2001,0,18,'middle','2001 low: 72'),(2025,8,4,'start','2025: 91')]:
            s+=f'<circle cx="{x(yr):.1f}" cy="{y(rr[yr]):.1f}" r="4" fill="var(--s1)" class="dot"/><text x="{x(yr)+dx:.1f}" y="{y(rr[yr])+dy:.1f}" class="lab" text-anchor="{a}">{t}</text>'
        return s
    o,x,y,W,H=line([('Real rail rate',rr,'var(--s1)','ln',0)],1969,2025,60,110,[60,70,80,90,100,110],[1970,1980,1990,2000,2010,2020],R=70,extra=ex)
    Bc=f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Inflation-adjusted rail freight rates, 1969 to 2025, indexed to 1980" class="chart">'+'\n'.join(o)+'</svg>'
    ix=pr.loc[2004:2025,['rail','truck','air','cpi']]; ix=ix/ix.iloc[0]*100
    o,x,y,W,H=line([('CPI',ix.cpi,'var(--muted)','ln ref',12),('Rail',ix.rail,'var(--s1)','ln',0),('Trucking',ix.truck,'var(--s2)','ln',-6),('Airfares',ix.air,'var(--s3)','ln',0)],2004,2025,80,220,[80,100,120,140,160,180,200,220],[2004,2008,2012,2016,2020,2024],R=130,labels=True)
    C=f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Price indexes for rail, trucking, airfares and consumer prices, 2004 equals 100" class="chart">'+'\n'.join(o)+'</svg>'
    A1=strip('margin',0,40,[0,10,20,30,40],'%','Average operating margin by firm, grouped by mode')
    A2=strip('roa',0,25,[0,5,10,15,20,25],'%','Average operating return on assets by firm, grouped by mode')
    rows=''.join(f'<tr><td>{r.firm}</td><td>{r["mode"]}</td><td class="n">{int(r.n)}</td><td class="n">{r.margin:.1f}</td><td class="n">{r.roa:.1f}</td><td class="n">{r.ppe_rev:.2f}</td><td class="n">{r.sd:.1f}</td></tr>' for _,r in fm.iterrows())

    # ---------- long-run charts ----------
    h=pd.read_csv(PROCESSED/'historical_rates.csv',index_col=0); h['real']=h.real_rate_1886_100; om=pd.read_csv(PROCESSED/'historical_margins.csv',index_col=0).iloc[:,0]
    def exD(x,y):
        s=''
        for yr,t in [(1887,'Interstate Commerce Act, 1887'),(1906,'Hepburn Act, 1906')]:
            s+=f'<line x1="{x(yr):.1f}" y1="{y(240):.1f}" x2="{x(yr):.1f}" y2="{y(0):.1f}" class="ann"/><text x="{x(yr)+6:.1f}" y="{y(240)+(10 if yr==1887 else 26):.1f}" class="tick">{t}</text>'
        for yr,dx,dy,a,t in [(1865,8,4,'start','1865: 219'),(1886,-6,16,'end','1886: 100'),(1916,0,18,'middle','1916: 47')]:
            s+=f'<circle cx="{x(yr):.1f}" cy="{y(h.real[yr]):.1f}" r="4" fill="var(--s1)" class="dot"/><text x="{x(yr)+dx:.1f}" y="{y(h.real[yr])+dy:.1f}" class="lab" text-anchor="{a}">{t}</text>'
        return s
    o,x,y,W,H=line([('Real freight rate',h.real,'var(--s1)','ln',0)],1865,1955,0,240,[0,40,80,120,160,200,240],[1870,1880,1890,1900,1910,1920,1930,1940,1950],R=70,extra=exD)
    o.append(f'<text x="{x(1955)+9:.1f}" y="{y(h.real[1955])+4:.1f}" class="lab">1955: 37</text>')
    Dc=f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Inflation-adjusted rail freight revenue per ton-mile, 1865 to 1955, indexed to 1886" class="chart">'+'\n'.join(o)+'</svg>'
    # E: miles built bars
    b=fred('A02F2AUSA374NNBR')
    W,H,L,R,T,B=720,300,48,16,16,30; x=lambda v:L+(v-1830)/(1953-1830)*(W-L-R); y=lambda v:T+(14000-v)/14000*(H-T-B); bw=(W-L-R)/123-1
    o=[f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Miles of railroad built per year in the United States, 1830 to 1952" class="chart">']
    for a,c in [(1857,1860),(1873,1878),(1884,1886)]: o.append(f'<rect x="{x(a):.1f}" y="{T}" width="{x(c)-x(a):.1f}" height="{H-T-B}" class="band"/>')
    for t in [0,4000,8000,12000]: o.append(f'<line x1="{L}" y1="{y(t):.1f}" x2="{W-R}" y2="{y(t):.1f}" class="grid"/><text x="{L-6}" y="{y(t)+4:.1f}" class="tick" text-anchor="end">{t:,}</text>')
    for t in range(1840,1951,10): o.append(f'<text x="{x(t)+bw/2:.1f}" y="{H-B+18}" class="tick" text-anchor="middle">{t}</text>')
    for k,v in b.items(): o.append(f'<rect x="{x(k):.1f}" y="{y(v):.1f}" width="{bw:.1f}" height="{max(y(0)-y(v),0.5):.1f}" fill="var(--s1)"><title>{k}: {int(v):,} miles</title></rect>')
    o.append(f'<line x1="{L}" y1="{y(0)}" x2="{W-R}" y2="{y(0)}" class="axis"/>')
    for k,a,dx in [(1872,'end',-4),(1882,'end',-4),(1887,'start',8)]: o.append(f'<text x="{x(k)+dx:.1f}" y="{y(b[k])+4:.1f}" class="lab" text-anchor="{a}">{k}: {int(b[k]):,}</text>')
    o.append('</svg>'); E='\n'.join(o)
    # F: operating margin 1908-1961 and 2007-2025
    raw=pd.read_csv(PROCESSED/'firm_panel.csv'); mod=raw[(raw['mode']=='Rail')&(raw.year<=2025)].groupby('year').margin.mean()
    def exF(x,y):
        s=''
        for a,c,t in [(1918,1920,'Federal control'),(1941,1945,'WWII')]: s+=f'<rect x="{x(a):.1f}" y="{y(45):.1f}" width="{x(c)-x(a):.1f}" height="{y(0)-y(45):.1f}" class="band"/><text x="{(x(a)+x(c))/2:.1f}" y="{y(45)+12:.1f}" class="tick" text-anchor="middle">{t}</text>'
        s+=f'<text x="{x(1985):.1f}" y="{y(24):.1f}" class="tick" text-anchor="middle">no comparable series</text><text x="{x(1985):.1f}" y="{y(24)+14:.1f}" class="tick" text-anchor="middle">on FRED, 1962–2006</text>'
        s+=f'<text x="{x(1906.5):.1f}" y="{y(38.5):.1f}" class="lab">1908–16: 31.5%</text><text x="{x(1953):.1f}" y="{y(14):.1f}" class="lab" text-anchor="middle">1946–61: 21.9%</text><text x="{x(2014):.1f}" y="{y(42):.1f}" class="lab" text-anchor="middle">2009–25: 33%</text>'
        return s
    o,x,y,W,H=line([('All Class I railroads',om,'var(--s1)','ln',0),('Five large railroads',mod,'var(--s1)','ln',0)],1905,2026,0,45,[0,10,20,30,40],[1910,1930,1950,1970,1990,2010],R=24,extra=exF)
    F=f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Railroad operating margin, 1908 to 1961 and 2007 to 2025" class="chart">'+'\n'.join(o)+'</svg>'
    return dict(A1=A1,A2=A2,B=Bc,C=C,D=Dc,E=E,F=F,rows=rows)


STANDALONE_COLORS = {"var(--s1)": "#2a78d6", "var(--s2)": "#eb6834", "var(--s3)": "#1baf7a", "var(--muted)": "#7d8591"}
STANDALONE_STYLE = """<style>
text{font-family:Inter,system-ui,-apple-system,'Segoe UI',sans-serif}
.grid{stroke:#dfe3e9;stroke-width:1}.axis{stroke:#b9c0ca;stroke-width:1}
.tick{fill:#7d8591;font-size:11px}.lab{fill:#4a515c;font-size:12px}.val{fill:#14171c;font-size:12px;font-weight:600}
.dot{stroke:#ffffff;stroke-width:2}.mean{stroke:#14171c;stroke-width:2}
.ln{stroke-width:2;stroke-linejoin:round;stroke-linecap:round}.ref{stroke-dasharray:4 4}
.ann{stroke:#b9c0ca;stroke-width:1;stroke-dasharray:3 3}.band{fill:#dfe3e9;opacity:.55}
</style><rect width="100%" height="100%" fill="#ffffff"/>"""
FILES = {"A1": "fig1a_operating_margin_by_firm", "A2": "fig1b_return_on_assets_by_firm",
         "B": "fig2_real_rail_rates_1969_2025", "C": "fig3_price_indexes_2004_2025",
         "E": "fig4_miles_built_1830_1952", "D": "fig5_real_freight_rates_1865_1955",
         "F": "fig6_rail_operating_margin_1908_2025"}


def main():
    figs = build()
    FIGURES.mkdir(parents=True, exist_ok=True)
    for key, name in FILES.items():
        svg = figs[key].replace('class="chart">', 'xmlns="http://www.w3.org/2000/svg">' + STANDALONE_STYLE, 1)
        for var, hexv in STANDALONE_COLORS.items():
            svg = svg.replace(var, hexv)
        (FIGURES / f"{name}.svg").write_text(svg)
        print(f"figures/{name}.svg")


if __name__ == "__main__":
    main()
