from Shen_np import *
from wuli import *
from creature import *
import os,time

def mase(x,y):
    a=((x-y)**2).sum()
    if a.data[0]<1:
        return a
    else:
        return a**0.5

def entropy(x):
    return Ten([-1]).expand(len(x))*x*x.log()

def clip(x,maxx,minx):
    p=[]
    for i in range(len(x)):
        if x.data[i]>maxx:
            p.append(Ten([maxx]))
        elif x.data[i]<minx:
            p.append(Ten([minx]))
        else:
            p.append(x.cut(i,i+1))
    return Ten.connect(p)

def minten(x,y):
    p=[]
    for i in range(len(x)):
        if x.data[i]<=y.data[i]:
            p.append(x.cut(i,i+1))
        else:
            p.append(y.cut(i,i+1))
    return Ten.connect(p)

class env(Environment):
    def __init__(self):
        Phy.biao=[]
        super().__init__([eval(evnname+"()")],
                         g=650,
                         groundhigh=-50,
                         groundk=10000,
                         grounddamp=100,
                         randsigma=0.1,
                         dampk=0.08,
                         friction=650)
        for i in self.creatures[0].muscles:
            i.stride=3
            i.damk=20
        self.r=0

    def getstat(self):  #box21 leg35
        s=self.creatures[0].getstat(False,pk=0.023,vk=0.028,ak=0.001,mk=0.05)
        return s

    def act(self,a):
        self.creatures[0].actdisp(a)

    def reward(self):
        return self.r

    def show(self,m):
        e=env()
        Phy.tready()
        ar=0
        for i in range(250):
            a=m.choice(e.getstat())
            e.act(a)
            e.step(0.001)
            ar+=e.reward()
            turtle.goto(-800,ground)
            turtle.pendown()
            turtle.goto(800,ground)
            turtle.penup()
            Phy.tplay()
            if e.isend():
                break
            time.sleep(0.01)
        print(ar)

    def step(self,t):
        v=0
        v2=0
        p=0
        std=0.668930899
        mean=0.103502928
        for i in range(30):
            super().step(t)
            # p+=sum([i.p[1] for i in self.creatures[0].phys])/len(self.creatures[0].phys)
            #v2+=sum([i.v[1] for i in self.creatures[0].phys])/len(self.creatures[0].phys)
            v+=sum([i.v[0] for i in self.creatures[0].phys])/len(self.creatures[0].phys)
            # p-=sum([1 if (i.x>=i.originx*i.maxl or i.x<=i.originx*i.minl) else 0 for i in self.creatures[0].muscles])*10
        self.r=(v**0.5/90 if v>1 else 0)-(10 if self.isend(3) else 0)#+v2/120
        self.r=(self.r-mean)/std
        # self.r=p/10000
    
    def test(self):
        e=env()
        ar=0
        for i in range(500):
            e.act([random.randint(0,1) for i in range(musclenum)]) #[0,1] if e.creatures[0].phys[3].p[0]<0 else [1,0]
            e.step(0.001)
            ar+=e.reward()
            p=0
            v=0
            a=0
            m=0
            for i in e.creatures[0].phys:
                p+=(i.p[0]+i.p[1])/2
                v+=(i.v[0]+i.v[1])/2
                a+=(i.axianshi[0]+i.axianshi[1])/2
            for i in e.creatures[0].muscles:
                m+=distant(i.p1,i.p2)
            p/=len(e.creatures[0].phys)
            v/=len(e.creatures[0].phys)
            a/=len(e.creatures[0].phys)
            m/=len(e.creatures[0].muscles)
            print(e.reward(),p,v,a,m)
            if e.isend():
                break
    
    def isend(self,h=1):
        for i in self.creatures[0].phys:
            if i.p[1]>h+self.ground:
                return False
        return True

class model:
    def __init__(self):
        self.f1=Linear(statnum, 256)
        self.f2=Linear(256,musclenum*2)

    def forward(self,x):
        x=self.f1(x).relu()
        x=self.f2(x)
        x=Ten.connect([x.cut(i*2,i*2+2).softmax() for i in range(len(x)//2)])
        return x

    def choice(self,x):
        v = self.forward(x).data
        a=[]
        # print(v)
        for i in range(len(v)):
            if i%2==1:
                continue
            v2=v[i:i+2]
            a.append(v2.index(random.choices(v2,v2)[0]))
        Operator.clean()
        return a

    def optimize(self,k=0.01):
        self.f1.grad_descent_zero(k)
        self.f2.grad_descent_zero(k)

class modelv:
    def __init__(self):
        self.f1=Linear(statnum, 256)
        self.f2=Linear(256,1)

    def forward(self,x):
        x=self.f1(x).relu()
        x=self.f2(x)
        return x

    def optimize(self,k=0.01):
        self.f1.grad_descent_zero(k)
        self.f2.grad_descent_zero(k)

    def dcopy(self):
        c=modelv()
        c.f1=self.f1.dcopy()
        c.f2=self.f2.dcopy()
        return c

class memory:
    def __init__(self,maxsize=10):
        self.memo=[]
        self.maxsize=maxsize
    
    def experience(self,m,times=3,n=500):
        for t in range(times):
            e=env()
            exp=[]
            ar=0
            for i in range(n):
                s=e.getstat()
                
                v = m.forward(s).data
                a=[]
                p=[]
                for j in range(len(v)):
                    if j%2==1:
                        continue
                    v2=v[j:j+2]
                    a.append(v2.index(random.choices(v2,v2)[0]))
                    p.append(v2[a[-1]])
                Operator.clean()
                
                e.act(a)
                e.step(0.001)
                st=e.getstat()
                r=e.reward()
                ar+=r
                exp.append([s,a,r,st,0,p])
                if i==n-1 or e.isend():
                    exp[-1][4]=1
                    break
            self.memo.append(exp)
        if len(self.memo)>self.maxsize:
            self.memo=self.memo[-self.maxsize:]
        return ar/times

def train(m, mv, memo, n=200, times=1,discount=0.99,lamb=0.99, ek=0.5,eps=0.2):
    ar=memo.experience(m,times,n=n)
    aloss=0
    alossv=0
    aloss=0
    alossv=0
    alosse=0
    alratio=0
    count=0
    for exp in memo.memo:
        c=0
        ad=[]
        gae=0
        for i in range(len(exp)-1,-1,-1):
            v=mv.forward(exp[i][0]).data[0]
            v2=mv.forward(exp[i][3]).data[0]
            tdd=exp[i][2]+discount*v2*(1-exp[i][4])-v
            gae=tdd+lamb*discount*gae*(1-exp[i][4])
            ad.append(gae)
            Operator.clean()
        ad.reverse()
        # mean=sum(ad)/len(ad)
        # std=sum([(a-mean)**2 for a in ad])**0.5
        
        for i in exp:
            s,a,r,st,end,p=i
            out=m.forward(s)
            pc=Ten.connect([out.cut(a[j]+j*2,a[j]+j*2+1) for j in range(len(a))])
            # ent=Ten.connect([entropy(out.cut(j*2,j*2+1))+entropy(out.cut(1+j*2,1+j*2+1)) for j in range(len(a))])
            ent=entropy(out).sum()
            v=mv.forward(s)
            adv=Ten([ad[c]])

            ratio=(pc.log()-Ten(p).log()).exp()
            surr=ratio*adv.expand(len(pc))
            surr2=clip(ratio,1+eps,1-eps)*adv.expand(len(pc))
            
            loss=Ten([-1]).expand(len(pc))*(minten(surr,surr2))#+Ten([-ek]).expand(len(pc))*ent
            loss.onegrad()
            losse=Ten([-ek])*ent
            losse.onegrad()
            
            aloss+=sum([i for i in loss.data])/len(loss)
            alosse+=ent.data[0]/len(out)
            alratio+=sum([abs(i-1) for i in ratio.data])/len(loss)
            lossv=mase(v,Ten((adv-v).data))
            alossv+=lossv.data[0]
            # if abs(lossv.data[0]) > 80:
            #     print(f"loss-v{lossv.data[0]},梯度过高")
            #     Operator.clean()
            #     continue
            Operator.back()
            count+=1
            c+=1
    m.optimize(0.0008/count)#0.0005
    mv.optimize(0.0008/count)
    print(ar,aloss/count,alossv/count,alosse/count,alratio/count)
    return ar,aloss/count,alossv/count,alosse/count

evnname="box2"
e=env()
statnum=len(e.getstat())
musclenum=sum([len(i.muscles) for i in e.creatures])
ground=e.ground
del e
savename=f"rlt-3-ppo-{evnname}-n"
if savename in os.listdir():
    print("load",savename)
    Layer.loadall(savename)
m=model()
mv=modelv()
memo=memory(2)
Layer.issave=False
maxr=6000

mode=0
while True:
    if mode:
        try:
            r,al,av,ae=train(m,mv,memo,discount=0.98,ek=0.3,n=250)
        except OverflowError:
            r=0
            print("OverflowError")
            memo.memo=[]
            Operator.clean()
            pass
        if r>maxr:
            maxr=r
            Layer.saveall(savename+f"{r}")

        Layer.saveall(savename)
    else:
        e=env()
        e.show(m)
        # e.test()

