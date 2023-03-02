import numpy as np
import cv2
import soundcard as sc        # Get it from https://github.com/bastibe/SoundCard
imWidth, imHeight = 512, 512                       # screen size

import matplotlib
matplotlib.use('WebAgg')
from matplotlib import pyplot as plt
plt.ion()

import sys, time


numframes = imWidth
samplerate = 44100

# Bordi per accettare il picco
minFrame = 100
maxFrame = numframes-minFrame




import signal

def handler(signum, frame):
    print(h)
    print(binc)
    print("Ciao Ciao....")
    # Implementare salvataggio dati...
	
    res = input("Inserisci il nome del file, invio per non salvare:\t")
    
    print(f"res vale: {res}")
    if res != "":
        np.savetxt(f"./data/{res}.dat", (binc, h), delimiter = "\t")
        
    plt.close("all")
    sys.exit()

signal.signal(signal.SIGINT, handler)





lstMax = []

def draw_wave(screen, mono_audio, xs, title="oscilloscope", gain=.8):
    screen *= 0                                     # clear the screen
    ys = imHeight/2*(1 - np.clip( gain * mono_audio[0:len(xs)], -1, 1))  # the y-values of the waveform
    pts = np.array(list(zip(xs,ys))).astype(np.int) # pair up xs & ys
    cv2.polylines(screen,[pts],False,(0,255,0))     # connect points w/ lines
    
    ythr = imHeight/2*(1 - np.clip( gain * np.ones(len(xs)) * thr, -1, 1))
    ptsthr = np.array(list(zip(xs,ythr))).astype(int) # pair up xs & ys
    cv2.polylines(screen,[ptsthr],False,(255,0,0))     # connect points w/ lines
    
    
    maxvaly = np.max(mono_audio)
    xmax = np.argmax(mono_audio)
    
    
    # max orizzontale
    ymax = imHeight/2*(1 - np.clip( gain * np.ones(len(xs)) * maxvaly, -1, 1))
    ptsmax = np.array(list(zip(xs,ymax))).astype(int) # pair up xs & ys
    cv2.polylines(screen,[ptsmax],False,(0,0,255))     # connect points w/ lines
    
    
    #max verticale
    x = np.ones(imHeight) * xmax
    y = np.arange(imHeight).astype(np.int)  
    ptsmaxv = np.array(list(zip(x,y))).astype(int) # pair up xs & ys
    cv2.polylines(screen,[ptsmaxv],False,(0,0,255))     # connect points w/ lines

    
    cv2.imshow(title, screen)                       # show what we've got
    
    
    lstMax.append(maxvaly - np.mean(mono_audio))


default_mic = sc.default_microphone()
screen = np.zeros((imHeight,imWidth,3), dtype=np.uint8) # 3=color channels
xs = np.arange(imWidth).astype(int)                  # x values of pixels

thr = 0.35

# Figura spettro
figSp, axSp = plt.subplots()
axSp.grid()

axSp.set_xlabel("Energia", fontsize = 14)
axSp.set_ylabel("Conteggi", fontsize = 14)

lineSp, = axSp.plot(np.ones(100), np.ones(100), c = "tab:green", ds = "steps-mid", label = "Spettro")

#plt.show()



conteggi = 0
dutyCyclePercent = 0
inizio = time.time()

tRefresh = time.time()

while (1):                               # keep looping until someone stops this
    tIni = time.time() # Tempo inizio ciclo         




    with default_mic.recorder(samplerate=samplerate) as mic:
        audio_data = mic.record(numframes=numframes)  # get some audio from the mic
        
        
    if audio_data[:,0].max() > thr:
        
        # Se sono troppo ai bordi, lo rifiuto
        if not  (audio_data[:,0].argmax()>minFrame & audio_data[:,0].argmax()<maxFrame): continue
        
        
        # Dentro qui viene anche appeso alla lista
        draw_wave(screen, audio_data[:,0], xs)             # draw left channel
        
        conteggi +=1

        
        
        # Aggiorno ogni 5 secondi l'istogramma
        if (time.time() - tRefresh) > 5 :
            # Istogrammo i massimo
            h, bins = np.histogram(lstMax, bins = 100)
            binc = bins[:-1] + (bins[1] - bins[0]) / 2
            
            # Disegno
            lineSp.set_xdata(binc)    
            lineSp.set_ydata(h)    
            
            
            # Conto e aggiorno il rate
            #conteggi +=1
            figSp.suptitle(f"Rate: {conteggi/(time.time()-inizio):.2f} Hz\t Duty cycle {dutyCyclePercent:.2f} %")

            
            figSp.canvas.draw()
            figSp.canvas.flush_events()    
            
            axSp.set_xlim(binc.min(), binc.max())
            axSp.set_ylim(0, h.max()+2)
            
            tRefresh = time.time()
        
        
    # Dopo 5 secondi, riparto
    if time.time()-inizio >5:
        inizio = time.time()
        conteggi = 0
    dutyCyclePercent = numframes/samplerate / (time.time() - tIni) * 100

        
        
        
    key = cv2.waitKey(1) & 0xFF                        # keyboard input
    if ord('q') == key:                                # quit key
        break
        
        
        
   
