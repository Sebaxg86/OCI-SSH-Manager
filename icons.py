"""Iconos de contorno, dibujados localmente; sin fuentes ni emojis."""
import base64
import math
import struct
import zlib
import tkinter as tk

PATHS = {
 'folder': [[(2,5),(2,3),(7,3),(9,5),(14,5),(14,13),(2,13),(2,5)]],
 'folder_add': [[(2,5),(2,3),(7,3),(9,5),(14,5),(14,13),(2,13),(2,5)],[(8,7),(8,11)],[(6,9),(10,9)]],
 'add': [[(2,2),(11,2),(11,6)],[(2,2),(2,14),(8,14)],[(7,10),(15,10)],[(11,6),(11,14)]],
 'edit': [[(3,10),(10,3),(13,6),(6,13),(2,14),(3,10)],[(8,5),(11,8)]],
 'archive': [[(2,5),(2,14),(14,14),(14,5)],[(1,2),(15,2),(15,5),(1,5),(1,2)],[(6,8),(10,8)]],
 'connect': [[(10,2),(14,2),(14,14),(10,14)],[(1,8),(11,8)],[(7,4),(11,8),(7,12)]],
 'terminal': [[(1,3),(15,3),(15,13),(1,13),(1,3)],[(4,6),(6,8),(4,10)],[(8,10),(12,10)]],
 'grip': [[(3,4),(13,4)],[(3,8),(13,8)],[(3,12),(13,12)]],
 'save': [[(2,8),(6,12),(14,4)]],
 'cancel': [[(4,4),(12,12)],[(12,4),(4,12)]],
 'filter': [[(2,4),(14,4)],[(4,8),(12,8)],[(6,12),(10,12)]],
 'refresh': [[(8+5*math.cos(t),8+5*math.sin(t)) for t in [i*0.16 for i in range(5,38)]],[(10,2),(14,3),(13,7)]],
}

def outline_icon(name, master, size=16, color=(142,142,147)):
    scale = 4
    pixels = bytearray(size*size*4)
    segments = [(a,b) for path in PATHS[name] for a,b in zip(path,path[1:])]
    def hits(x,y,a,b):
        dx,dy=b[0]-a[0],b[1]-a[1]
        length=dx*dx+dy*dy
        t=max(0,min(1,((x-a[0])*dx+(y-a[1])*dy)/length)) if length else 0
        return (x-a[0]-t*dx)**2+(y-a[1]-t*dy)**2 <= 0.65**2
    for y in range(size):
        for x in range(size):
            coverage=0
            for sy in range(scale):
                for sx in range(scale):
                    xx=(x+(sx+0.5)/scale)*16/size
                    yy=(y+(sy+0.5)/scale)*16/size
                    coverage += any(hits(xx,yy,a,b) for a,b in segments)
            offset=(y*size+x)*4
            pixels[offset:offset+4]=bytes((*color,round(255*coverage/(scale*scale))))
    def chunk(kind,data):
        return struct.pack('!I',len(data))+kind+data+struct.pack('!I',zlib.crc32(kind+data)&0xffffffff)
    rows=b''.join(b'\0'+pixels[y*size*4:(y+1)*size*4] for y in range(size))
    png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!IIBBBBB',size,size,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(rows))+chunk(b'IEND',b'')
    return tk.PhotoImage(master=master,data=base64.b64encode(png).decode(),format='png')

def load_icons(master):
    return {name:outline_icon(name,master) for name in PATHS}
