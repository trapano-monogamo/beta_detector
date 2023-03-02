# Original link: https://gist.github.com/drscotthawley/7c0a8b0f95d2c101ea3392ed6af85a63


# Allows debug on spyder in my spyder-cf environment
#import collections
#collections.Callable = collections.abc.Callable

import sys

import numpy as np
from matplotlib import pyplot as plt
plt.ion()

# Microfono
import soundcard as sc        # Get it from https://github.com/bastibe/SoundCard
default_mic = sc.default_microphone()



# Tempo
import time
inizio = time.time()
conteggi = 0





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





# Figura segnale
fig, axv = plt.subplots(2,1)
fig.subplots_adjust(hspace = .4)
ax = axv[0]
axs = axv[1]

ax.set_ylim(-.1, .3)
ax.set_ylim(-1, 2.5)
axs.set_ylim(-.1, .5)
axs.set_ylim(-.2, .2)

for a in axv:
    a.grid()


ax.set_xlabel("Time [tick]", fontsize = 14)
ax.set_ylabel("Ampiezza", fontsize = 14)



# Figura spettro
figSp, axSp = plt.subplots()
axSp.grid()

axSp.set_xlabel("Energia", fontsize = 14)
axSp.set_ylabel("Conteggi", fontsize = 14)



# vettore spettro
lstMax = []



# Settings
thr = 0.04
thr = 0.15
gain = 5

samplerate = 44100*4
numframes = 1024

minFrame = 100
maxFrame = numframes-minFrame


# X values
xs = np.arange(numframes).astype(int)             


# Inizializzo le curve
ysThr = np.ones(numframes)*thr
line1, = ax.plot(xs, ysThr, "g-", label = "Data") # Data
line2, = ax.plot(xs, ysThr, "r--", label = f"Thr={thr}") # Thr

lineSh, = axs.plot(xs, ysThr, ls = "-", c = "tab:green", label = "Data") # shaped
vline = axs.axvline(x = 0, ls = ":", c = "k")
hline = axs.axhline(y = 0, ls = ":", c = "k")


lineSp, = axSp.plot(np.ones(100), np.ones(100), c = "tab:green", ds = "steps-mid", label = "Spettro")


#lineSp, = axSp.plot(np.ones(100), np.ones(100), ds = "steps-mid", c = "darkgreen", lw = 2, label = "APC 1")
#lineSp2 = axSp.fill_between(np.ones(100), np.ones(100), step = "mid", color = "lime", alpha = 1)


ax.legend()
axSp.legend()





dutyCyclePercent = 0

while (1):          

    tIni = time.time() # Tempo inizio ciclo                    
    
    with default_mic.recorder(samplerate = samplerate) as mic:
        audio_data = mic.record(numframes = numframes)  # get some audio from the mic
        
        
    # Verifico se ho superato la soglia    
    if not  audio_data[:,0].max()>thr:
        continue
    if not  (audio_data[:,0].argmax()>minFrame & audio_data[:,0].argmax()<maxFrame):
        continue
    
    
    # Conto e aggiorno il rate
    conteggi +=1
    fig.suptitle(f"Rate: {conteggi/(time.time()-inizio):.2f} Hz\t Duty cycle {dutyCyclePercent:.2f} %")
    
    # Dopo 5 secondi, riparto
    if time.time()-inizio >5:
        inizio = time.time()
        conteggi = 0
    
    # Disegno la curva corretta
    ys = audio_data #Usless
    
    
    # Aggiorno i punti e li disegno
    line1.set_ydata(ys)    

    # fig.canvas.draw()
    # fig.canvas.flush_events()    
    
    
    # Mi memorizzo il massimo
    ##lstMax.append(ys.max())
    
    
    
    
    
    
    # RC4
    ys = ys - ys.mean()
    decay_time = 10
    factor = np.exp(-1 / decay_time)
    
    a0 = (1.0 - factor) * (1.0 - factor) * (1.0 - factor) * (1.0 - factor)
    b1 =  4. * factor
    b2 = -6. * factor * factor
    b3 =  4. * factor * factor * factor
    b4 = -1. * factor * factor * factor * factor
    
    
    #shaped = a0 * ys[4:] + b1 * ys[3:-1] + b2 * ys[2:-2] + b3 * ys[1:-3] + b2 * ys[0:-4]
    
    shaped = np.zeros(numframes)
    shaped[0] = 0 # Ossimoro
    for i in np.arange(numframes):
        x_i = audio_data[i,0]
        y_i_minus_one = shaped[i-1] if (i-1) > 0 else 0
        y_i_minus_two = shaped[i-2] if (i-2) > 0 else 0 
        y_i_minus_three  = shaped[i-3] if (i-3) > 0 else 0 
        y_i_minus_four  = shaped[i-4] if (i-4) > 0 else 0 
        
        
        shaped[i] = a0 * x_i + b1 * y_i_minus_one + b2 * y_i_minus_two + b3 * y_i_minus_three + b4 * y_i_minus_four
    
    
    # Aggiorno i punti e li disegno
    lineSh.set_ydata(shaped)    
    vline.set_xdata(xs[np.argmax(shaped)] * np.ones(2))    
    hline.set_ydata(np.max(shaped) * np.ones(2))    
    
    fig.canvas.draw()
    fig.canvas.flush_events()    
    
    
    # Mi memorizzo il massimo
    lstMax.append(shaped.max())

    
    
    
    
    
    
    # Istogrammo i massimo
    h, bins = np.histogram(lstMax, bins = 100)
    binc = bins[:-1] + (bins[1] - bins[0]) / 2
    
    # Disegno
    lineSp.set_xdata(binc)    
    lineSp.set_ydata(h)    
    
    figSp.canvas.draw()
    figSp.canvas.flush_events()    
    
    axSp.set_xlim(binc.min(), binc.max())
    axSp.set_ylim(0, h.max()+2)
    
    
    #print(f"Ho acquisito per {numframes/samplerate * 1e3:.2f} ms, mentre il ciclo è durato {(time.time() - tIni) * 1e3:.2f} ms\nRapporto = {numframes/samplerate / (time.time() - tIni) * 100}%\n")
    # Duty cycle percentuale
    dutyCyclePercent = numframes/samplerate / (time.time() - tIni) * 100
    
    

    
