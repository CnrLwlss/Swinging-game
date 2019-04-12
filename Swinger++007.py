import pygame
import sqlite3
import math
import random

### Adjustables (see also the 1st and last sections of __init__ of the human class
## Colours
# Background
bgInteract=(163,200,255)
bgDull=(133, 168, 255)
bgFloor=(163, 200, 100)

# Enemies
typCol=((203,80,82), (255,231,217))

# Player
plyCol=(66,67,89)
strCol=(0,0,0)
hpCol=((150,255,59), (200,200,200))

## Other
# Screen and framerate
fps=60
screenX=1600
screenY=900

#S caling
scale=30#               px/m
tileSize=2*scale
damageScale=200

pygame.init()
clock=pygame.time.Clock()
screen=pygame.display.set_mode((screenX,screenY))

#For typ==0: self.main
mX=0
mY=1
mRad=2# (radius)
mTyp=3# (type)
mRot=4# (rotation speed (entered as rotations per second, stored as radians per frame)
mDir=5# (Direction (1 (anticlockwise), or -1 (clockwise)
mDed=6# (dead)

#For typ==0: self.sub
sRad=0# (radius)
sDst=1# (distance)
sTyp=2# (type)
sX=3
sY=4
sAng=5# (angle)
sDed=6# (dead)

def hyp(x, y, X, Y):
    return (((X-x)**2)+((Y-y)**2))**(1/2)

def checkT_circRect(rx, ry, w, h, cx, cy, r):#r for rectangle, c for circle
    touch=False
    for i in range(4):
        if i==0:
            rX=rx
            rY=ry
        elif i==1:
            rX=rx+w
            rY=ry
        elif i==2:
            rX=rx
            rY=ry+h
        elif i==3:
            rX=rx+w
            rY=ry+h
        if hyp(cx, cy, rX, rY)<=r:
            touch=True
    if not touch:
        if rx<=cx<=rx+w and ry-r<=cy<=ry+h+r:
            touch=True
    if not touch:
        if ry<=cy<=ry+h and rx-r<=cx<=rx+w+r:
            touch=True
    return touch

class human():
    def __init__(self):
        self.hp=500
        self.hpMax=500
        self.hpParts=5
        self.hpPart=self.hpMax/self.hpParts
        self.mass=80#                   kg
        self.height=round(scale*1.65)#  px
        self.width=round(scale*0.6)#    px
        self.swinging=False

        self.x=40*scale
        self.y=-2*scale
        self.oldX=self.x
        self.oldY=self.y
        self.pivotX=0
        self.pivotY=0
        self.radius=(((self.pivotY-self.y)**2)+((self.pivotX-self.x)**2))**(1/2)
        self.fX=0
        self.fY=0
        self.chX=0
        self.chY=0

        self.jumpForce=6*scale#             N
        self.runForce=(12*scale)/fps#       N/frame
        self.boostForce=(12*scale)/fps#     N/frame
        self.runLimit=(6*scale)/fps#        px/frame  (all these are maybe incorrect since adding 
        self.runFriction=30000/(fps*scale)# N/frame    scale to them, feel free to correct)

    def gravity(self,fps):
        self.fY+=(0.1962*self.mass*scale)/fps

    def place(self):
        self.chX=self.x-self.oldX
        if self.y==-self.height:
            if self.chX<-self.runLimit:
                self.chX=-self.runLimit
            elif self.chX>self.runLimit:
                self.chX=self.runLimit
        self.oldX=self.x
        self.chX+=self.fX/self.mass
        self.x+=self.chX

        self.chY=self.y-self.oldY
        self.oldY=self.y
        self.chY+=self.fY/self.mass
        self.y+=self.chY
        if self.y>-self.height:
            self.y=-self.height

        self.fX=0
        self.fY=0

    def swing(self):
        dist=hyp(self.x, self.y, self.pivotX, self.pivotY)
        if dist>self.radius:
            ratio=self.radius/dist
            self.x=self.pivotX-((self.pivotX-self.x)*ratio)
            self.y=self.pivotY-((self.pivotY-self.y)*ratio)

    def latch(self,pos):
        self.pivotX=pos[0]
        self.pivotY=pos[1]
        self.radius=hyp(self.x, self.y, self.pivotX, self.pivotY)
        self.swinging=True

    def boost(self):
        chTotal=((self.chX**2)**(1/2))+((self.chY**2)**(1/2))
        self.fX+=(self.chX/chTotal)*self.boostForce
        self.fY+=(self.chY/chTotal)*self.boostForce

    def draw(self):
        pygame.draw.rect(screen, plyCol, pygame.Rect((screenX//2)-(self.width//2), (screenY//2)-(self.height//2), self.width, self.height))
        if self.swinging:
            pygame.draw.line(screen, strCol, (screenX//2, screenY//2), (self.pivotX-self.x+(screenX//2) ,self.pivotY-self.y+(screenY//2)), 1)
        extra=self.hpPart-(self.hp%self.hpPart)
        full=self.hp//self.hpPart
        for x in range(self.hpParts):
            if x==self.hpParts-full-1:
                if self.hp>0:
                    pygame.draw.rect(screen, hpCol[0], pygame.Rect(((screenX-self.hpMax-10)//2)+(x*(self.hpPart+2))+extra, 20, self.hpPart-extra, 20))
                pygame.draw.rect(screen, hpCol[1], pygame.Rect(((screenX-self.hpMax-10)//2)+(x*(self.hpPart+2)), 20, extra, 20))
            else:
                if x<self.hpParts-full-1:
                    col=hpCol[1]
                else:
                    col=hpCol[0]
                pygame.draw.rect(screen, col, pygame.Rect(((screenX-self.hpMax-10)//2)+(x*(self.hpPart+2)), 20, self.hpPart, 20))

class background():
    def __init__(self, lv=1):
        self.lv=lv
        self.blocks=(screenX//tileSize)+1
        with sqlite3.connect("Swinger++.db") as db:
            cursor=db.cursor()
            cursor.execute("SELECT * FROM level_"+str(self.lv))
            self.display=cursor.fetchall()

    def draw(self, x, y, w, h):
        tile=(x-((screenX+w)//2))//tileSize
        if tile<0:
            mod=-tile
            tile=0
        for r, R in enumerate(self.display):
            for c, C in enumerate(R[round(tile):round(tile+self.blocks+1)]):
                if C==1:
                    pygame.draw.rect(screen, bgInteract,
                                     pygame.Rect(((tile+c)*tileSize)-x+((screenX+w)//2),
                                                 screenY-((r+1)*tileSize)-h-y-(screenY//2)+(h//2),
                                                 tileSize,
                                                 tileSize))
        pygame.draw.rect(screen, bgFloor, pygame.Rect(0, screenY-h-y-(screenY//2)+(h//2), screenX, screenY//2))

class enemy():
    def __init__(self, typ=None, main=None, sub=None):
        self.typ=typ
        self.dead=False

        if self.typ==None:
            self.typ=random.randint(0,0)

        if self.typ==0:
            self.main=main
            self.main[mX]=round(self.main[mX]*tileSize)
            self.main[mY]=round(self.main[mY]*-tileSize)
            self.main[mRad]=round(self.main[mRad]*scale)
            self.main[mRot]=(self.main[mRot]*2*math.pi)/fps
            self.main.append(False)
            self.sub=sub
            self.squishTot=0
            if self.main[mTyp]==0:
                self.squishTot+=1
            if self.main[mRad]==0:
                self.main[mDed]=True
            if self.sub!=None:
                for i, I in enumerate(self.sub):
                    if I[sTyp]==0:
                        self.squishTot+=1
                    self.sub[i][sRad]=round(I[sRad]*scale)
                    self.sub[i][sDst]=round(I[sDst]*scale)
                    self.sub[i].append(self.main[mX])#                  X
                    self.sub[i].append(self.main[mY])#                  Y
                    self.sub[i].append((i*2*math.pi)/len(self.sub))#    Ang
                    self.sub[i].append(False)#                          Ded
                    if I[sRad]==0:
                        self.sub[i][sDed]=True

    def do(self):
        if self.typ==0:
            if self.sub!=None:
                for i, I in enumerate(self.sub):
                    self.sub[i][sAng]+=self.main[mRot]*self.main[mDir]
                    self.sub[i][sAng]=I[sAng]%(2*math.pi)
                    stage=I[sAng]//(math.pi/2)
                    if 0<=stage<=1:
                        multX=1
                    else:
                        multX=-1
                    if 1<=stage<=2:
                        multY=-1
                    else:
                        multY=1
                    remainder=I[sAng]%(math.pi/2)
                    if stage%2==1:
                        self.sub[i][sX]=self.main[mX]+(math.cos(remainder)*I[sDst]*multX)
                        self.sub[i][sY]=self.main[mY]+(math.sin(remainder)*I[sDst]*multY)
                    if stage%2==0:
                        self.sub[i][sX]=self.main[mX]+(math.sin(remainder)*I[sDst]*multX)
                        self.sub[i][sY]=self.main[mY]+(math.cos(remainder)*I[sDst]*multY)

    def be(self):
        if self.typ==0:
            pass

    def checkHit(self, x, y, w, h):
        hurtTot=0
        if not self.dead:
            if not self.main[mDed]:
                touch=checkT_circRect(x, y, w, h, self.main[mX], self.main[mY], self.main[mRad])
                if touch:
                    self.main[mDed]=True
                    if self.main[mTyp]==0:
                        self.squishTot-=1
                    else:
                        hurtTot+=self.main[mRad]
            if self.sub!=None:
                for i, I in enumerate(self.sub):
                    if not I[sDed]:
                        touch=checkT_circRect(x, y, w, h, I[sX], I[sY], I[sRad])
                        if touch:
                            self.sub[i][sDed]=True
                            if I[sTyp]==0:
                                self.squishTot-=1
                            else:
                                hurtTot+=I[sRad]
            if self.squishTot==0:
                self.dead=True
            hurtTot/=scale
        return hurtTot

    def think(self, x, y):
        if abs(x-self.main[mX])<=screenX and not self.dead:
            self.active=True
            self.do()
        else:
            self.active=False
            self.be()

    def draw(self, x, y, w, h):
        if not self.dead:
            modX=(screenX//2)-(w//2)-x
            modY=(screenY//2)-(h//2)-y
            if not self.main[mDed]:
                pygame.draw.circle(screen, typCol[self.main[mTyp]], (round(self.main[mX]+modX), round(self.main[mY]+modY)), self.main[mRad])
            if self.sub!=None:
                for I in self.sub:
                    if not I[sDed]:
                        pygame.draw.circle(screen, typCol[I[sTyp]], (round(I[sX]+modX), round(I[sY]+modY)), I[sRad])

def main():
    player=human()
    bg=background()
    
    enStartConditions=[[0, [15, 3, 0.8, 0, 1, 1/4], [[0.4, 1.6, 1]]],
                       [0, [26, 5, 0.8, 1, -1, 1/2], [[0.4, 1.6, 0], [0.4, 1.6, 0]]],
                       [0, [30, 2, 1.2, 1, 1, 1/6], [[0.2, 2, 1], [0.6, 2, 0]]],
                       [0, [40, 4, 0.4, 1, -1 ,1/8], [[0.2, 1.68, 0], [0.2, 1.2, 0], [0.2, 1.68, 0], [0.2, 1.2, 0], [0.2, 1.68, 1], [0.2, 1.2, 1], [0.2, 1.68, 1], [0.2, 1.2, 1]]],
                       [0, [45, 5, 1.6, 0, 1 ,1/16], [[0.4, 2.8, 0], [0.2, 2.4, 1], [0.2, 2.4, 1], [0.2, 2.4, 1], [0.2, 2.4, 1], [0.2, 2.4, 1], [0.2, 2.4, 1], [0.2, 2.4, 1]]],
                       [0, [50, 4, 0, 1, -1 ,1/4], [[0.8, 1.2, 0], [0.8, 1.2, 1]]]]
    """
    enStartConditions=[[0, [15, 3, 0.8, 0, 1, 1/4]],
                       [0, [26, 5, 0.8, 1, -1, 1/2]],
                       [0, [30, 2, 1.2, 1, 1, 1/6]],
                       [0, [40, 4, 0.4, 1, -1 ,1/8]],
                       [0, [45, 5, 1.6, 0, 1 ,1/16]],
                       [0, [50, 4, 0, 1, -1 ,1/4]]]
    """
    
    enList=[]
    for I in enStartConditions:
        enList.append(enemy(typ=I[0], main=I[1], sub=I[2]))
        #enList.append(enemy(typ=I[0], main=I[1]))

    pressA=False
    pressD=False
    pressSpace=False
    direction=""

    timer=0
    done=False
    while not done:
        screen.fill(bgDull)
        bg.draw(player.x, player.y, player.width, player.height)
        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                done=True

            if event.type==pygame.KEYDOWN:
                if event.key==pygame.K_a:
                    pressA=True
                elif event.key==pygame.K_d:
                    pressD=True
                elif event.key==pygame.K_SPACE:
                     pressSpace=True
                if player.y==-player.height:
                    if event.key==pygame.K_w:
                        player.fY-=player.jumpForce

            elif event.type==pygame.KEYUP:
                if event.key==pygame.K_a:
                    pressA=False
                elif event.key==pygame.K_d:
                    pressD=False
                elif event.key==pygame.K_SPACE:
                    pressSpace=False

            mPressed=pygame.mouse.get_pressed()
            pos=pygame.mouse.get_pos()
            edPos=[player.x+pos[0]-(screenX//2), player.y+pos[1]-(screenY//2)]
            if mPressed[0]:
                player.swinging=False
            if mPressed[2]:
                if screen.get_at(pos)[:3]==bgInteract:
                    player.latch(edPos)

        if player.y==-player.height:
            if pressA and not pressD:
                player.fX-=player.runForce
            elif pressD and not pressA:
                player.fX+=player.runForce
            else:
                player.fX-=(player.runFriction*player.chX)

        if pressSpace and player.swinging:
            player.boost()

        player.gravity(fps)
        player.place()
        if player.swinging:
            player.swing()
        for i in range(len(enList)):
            player.hp-=round(damageScale*(enList[i].checkHit(player.x, player.y, player.width, player.height)**2))
        if player.hp<0:
            player.hp=0
        for i in range(len(enList)):
            enList[i].think(player.x, player.y)

        for i in range(len(enList)):
            enList[i].draw(player.x, player.y, player.width, player.height)
        player.draw()
        pygame.display.update()

        if player.hp==0:
            done=True
        if timer==fps:
            timer=0
        else:
            timer+=1
        clock.tick(fps)

    done=False
    while not done:
        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                done=True

main()
pygame.quit()
