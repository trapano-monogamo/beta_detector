# Oscilloscope-v02a.py(w)  (13-10-2018)
# For Python version 3
# With external modules: numpy; pyaudio
# Created by Onno Hoekstra (pa2ohh)
import numpy
import pyaudio
import math
import time

from tkinter import *
from tkinter import messagebox
from tkinter import filedialog
from tkinter import simpledialog
from tkinter import font



# Values that can be modified
GRW = 1000                  # Width of the grid
GRH = 500                   # Height of the grid
X0L = 20                    # Left top X value of grid
Y0T = 25                    # Left top Y value of grid

SAMPLErate = 44100          # Sample rate of the soundcard 22050 44100 48000 96000

ADsens1 = 1000              # Sensitivity of AD converter CH1 1 V = 1000 levels
ADsens2 = 1000              # Sensitivity of AD converter CH2 1 V = 1000 levels

CHvdiv1x = [10.0, 20.0, 50.0, 100.0, 200.0, 500.0, 1000.0, 2000.0, 5000.0]   # Sensitivity list in mv/div

TIMEdiv1x = [0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 50.0, 100.0, 200.0, 500.0, 1000.0, 2000.0, 5000.0, 10000.0] # Time list in ms/div
TIMEdiv = 7                 # index 7 from TIMEdiv1x (20 ms) as initial value

ADzero = False              # Corrects the AD converter by taking the average of the Trace and offset it to zero.


# Colors that can be modified
COLORframes = "#000080"     # Color = "#rrggbb" rr=red gg=green bb=blue, Hexadecimal values 00 - ff
COLORcanvas = "#000000"
COLORgrid = "#808080"
COLORzeroline = "#0000ff"
COLORtrace1 = "#00ff00"
COLORtrace2 = "#ff8000"
COLORtext = "#ffffff"
COLORtrigger = "#ff0000"

# Button sizes that can be modified
Buttonwidth1 = 12
Buttonwidth2 = 8


# Initialisation of general variables
CH1div = len(CHvdiv1x) - 1  # last index from CHvdiv1x as initial value for channel 1
CH2div = len(CHvdiv1x) - 1  # last index from CHvdiv1x as initial value for channel 2

CH1probe = 1.0              # Probe attenuation factor 1x, 10x or 0.1x channel 1
CH2probe = 1.0              # Probe attenuation factor 1x, 10x or 0.1x channel 2

# Other global variables required in various routines
CANVASwidth = GRW + 2 * X0L # The canvas width
CANVASheight = GRH + 90     # The canvas height

Ymin = Y0T                  # Minimum position of screen grid (top)
Ymax = Y0T + GRH            # Maximum position of screen grid (bottom)

LONGsweep = False           # True if sweeps longer than 1 second
LONGchunk = LONGsweep       # True if chunk for longsweep is used for the trace

AUDIOsignal1 = []           # Audio trace channel 1    
AUDIOsignal2 = []           # Audio trace channel 2
AUDIOdevin = None           # Audio device for input. None = Windows default

T1line = []                 # Trace line channel 1
T2line = []                 # Trace line channel 2
Triggerline = []            # Triggerline

SHOWsamples = GRW           # Number of samples on the screen

SCstart = 0                 # Start sample of the trace
TRACES = 1                  # Number of traces 1 or 2
TRACESread = 0              # Number of traces that have been read from the audio stream

RUNstatus = 1               # 0 stopped, 1 start, 2 running, 3 stop and restart, 4 stop
AUDIOstatus = 0             # 0 audio off, 1 audio on

TRIGGERsample = 0           # Audio sample trigger point
TRIGGERlevel = 0            # Triggerlevel in samples


# =================================== Start widgets routines ========================================
def Bnot():
    print("Routine not made yet")


def BTriglevel1():
    global TRIGGERlevel
    global RUNstatus
    global SCREENrefresh
    global TRACErefresh
    
    td = ADsens1 * CHvdiv1x[CH1div] / 5000  
    TRIGGERlevel = int(TRIGGERlevel - td)
    if TRIGGERlevel < 0:
        TRIGGERlevel = 0
    UpdateTrace()           # Always Update
    

def BTriglevel2():
    global TRIGGERlevel
    global RUNstatus
    global SCREENrefresh
    global TRACErefresh
    
    Tmax = 5 * ADsens1 * CHvdiv1x[len(CHvdiv1x)-1] / 1000
    td = ADsens1 * CHvdiv1x[CH1div] / 5000  
    TRIGGERlevel = int(TRIGGERlevel + td)
    if TRIGGERlevel > Tmax:
        TRIGGERlevel = int(Tmax)
    UpdateTrace()           # Always Update
    

def BStart():
    global RUNstatus
    
    if (RUNstatus == 0):
        RUNstatus = 1
    UpdateScreen()          # Always Update


def BStop():
    global RUNstatus
    
    if (RUNstatus == 1):
        RUNstatus = 0
    elif (RUNstatus == 2):
        RUNstatus = 3
    elif (RUNstatus == 3):
        RUNstatus = 3
    elif (RUNstatus == 4):
        RUNstatus = 3
    UpdateScreen()          # Always Update


def Bprobe():
    global CH1probe
    global CH2probe
    global RUNstatus
    
    if (CH1probe == 0.1):
        CH1probe = 1
    elif (CH1probe == 1):
        CH1probe = 10
    elif (CH1probe == 10):
        CH1probe = 0.1
    CH2probe = CH1probe
    UpdateScreen()          # Always Update


def BSetup():
    global ADzero
    global SAMPLErate
    global RUNstatus
    global AUDIOsignal1
    global AUDIOsignal2
    global T1line
    global T2line
    
    s = simpledialog.askstring("Sample rate","Value: " + str(SAMPLErate) + "\n\nNew value:\n(22050, 44100, 48000, 96000, 192000)")

    if (s == None):         # If Cancel pressed, then None
        return()

    try:                    # Error if for example no numeric characters or OK pressed without input (s = ""), then v = 0
        v = int(s)
    except:
        v = 0

    if v != 0:
        SAMPLErate = v
        AUDIOsignal1 = []   # Reset Audio trace channel 1    
        AUDIOsignal2 = []   # Reset Audio trace channel 2
        T1line = []         # Reset trace line 1
        T2line = []         # Reset trace line 2
        
    ADzero = messagebox.askyesno("AD zeroing","AD offset correction mode on?", default = "no")    

    if (RUNstatus == 2):    # Restart if running
        RUNstatus = 4
    UpdateScreen()          # Always Update


def BView1():
    global SCstart
    global SAMPLErate
    global RUNstatus
    
    if (RUNstatus != 0):
        messagebox.showwarning("WARNING","Stop sweep first")
        return()

    SCstart = SCstart - SAMPLErate * 10 * TIMEdiv1x[TIMEdiv] / 2000 
    UpdateTrace()           # Always Update


def BView2():
    global SCstart
    global SAMPLErate
    global RUNstatus
        
    if (RUNstatus != 0):
        messagebox.showwarning("WARNING","Stop sweep first")
        return()

    SCstart = SCstart + SAMPLErate * 10 * TIMEdiv1x[TIMEdiv] / 2000
    UpdateTrace()           # Always Update
    
        
def BTime1():
    global TIMEdiv
    global RUNstatus
    
    if (TIMEdiv >= 1):
        TIMEdiv = TIMEdiv - 1

    if RUNstatus == 2:      # Restart if running
        RUNstatus = 4
    UpdateTrace()           # Always Update
    

def BTime2():
    global TIMEdiv1x
    global TIMEdiv
    global RUNstatus
    
    if (TIMEdiv < len(TIMEdiv1x) - 1):
        TIMEdiv = TIMEdiv + 1

    if RUNstatus == 2:      # Restart if running
        RUNstatus = 4
    UpdateTrace()           # Always Update
    

def BCH1level1():
    global CH1div
    global RUNstatus
    
    if (CH1div >= 1):
        CH1div = CH1div - 1
    UpdateTrace()           # Always Update
    

def BCH1level2():
    global CH1div
    global CHvdiv1x
    global RUNstatus
    
    if (CH1div < len(CHvdiv1x) - 1):
        CH1div = CH1div + 1
    UpdateTrace()           # Always Update
    

def BCH2level1():
    global CH2div
    global RUNstatus
    
    if (CH2div >= 1):
        CH2div = CH2div - 1
    UpdateTrace()           # Always Update

  
def BCH2level2():
    global CH2div
    global CHvdiv1x
    global RUNstatus
    
    if (CH2div < len(CHvdiv1x) - 1):
        CH2div = CH2div + 1
    UpdateTrace()           # Always Update
    

def BTraces():
    global TRACES
    global RUNstatus
    
    if (TRACES == 1):
        TRACES = 2
    else:
        TRACES = 1

    if RUNstatus == 2:      # Restart if running
        RUNstatus = 4
    UpdateTrace()           # Always Update
    

# ============================================ Main routine ====================================================
    
def AUDIOin():   # Read the audio from the stream and store the data into the arrays
    global AUDIOsignal1
    global AUDIOsignal2
    global AUDIOdevin
    global TRACES
    global TRACESread
    global RUNstatus
    global TIMEdiv1x
    global TIMEdiv
    global SAMPLErate
    global LONGsweep
    global LONGchunk
    global SCstart
    global TRACErefresh
    global SCREENrefresh
    global DCrefresh

 
    while (True):                                                   # Main loop
        PA = pyaudio.PyAudio()
        FORMAT = pyaudio.paInt16                                    # Audio format
        
        AUDIOsize = int(TRACES * SAMPLErate * TIMEdiv1x[TIMEdiv] * 10 / 1000)
        chunkbuffer = int(SAMPLErate)
        
        if AUDIOsize < SAMPLErate / 10:                             # Minimum time is 0.1 sec.
            AUDIOsize = SAMPLErate / 10
            
        if TIMEdiv1x[TIMEdiv] > 200:                                 # Long sweep if sweeptime > 2 second (200 ms/div)
            LONGsweep = True
        else:
            LONGsweep = False

        if LONGsweep == False:                                      # For shortsweeps, AUDIOsize is longer for trigger search and preview
            AUDIOsize = AUDIOsize * 1.5                             # 0.5 extra for trigger search

        # RUNstatus = 1 : Open Stream
        if (RUNstatus == 1):
            try:
                stream = PA.open(format = FORMAT,
                    channels = TRACES, 
                    rate = SAMPLErate, 
                    input = True,
                    output = False,
                    frames_per_buffer = int(chunkbuffer),
                    input_device_index = AUDIOdevin)
                LONGchunk = LONGsweep                               # If chunk and trace are for a long sweep, then set LONGchunk for trace information                  
                RUNstatus = 2
            except:                                                 # If error in opening audio stream, show error
                RUNstatus = 0
                txt = "Sample rate: " + str(SAMPLErate) + ", try a lower sample rate.\nOr another audio device."
                messagebox.showerror("Cannot open Audio Stream", txt)

        UpdateScreen()                                              # write to screen
    
        # RUNstatus = 2: Running
        if (RUNstatus == 2):
            signals = []
            AUDIOsignals = []

            try:
                buffervalue = stream.get_read_available()           # Buffer value
                if buffervalue > 1024:
                    signals = stream.read(buffervalue)              # Read samples from the buffer to make it empty
                while len(AUDIOsignals) < AUDIOsize:
                    buffervalue = stream.get_read_available()       # Buffer value
                    if buffervalue > 1024:                          # Prevent reading too small buffer sizes
                        signals = stream.read(buffervalue)          # Read samples from the buffer and extend to AUDIOsignal
                        AUDIOsignals.extend(numpy.fromstring(signals, "Int16"))
            except:
                RUNstatus = 4                                       # Error, restart

            # Start conversion audio samples to values -32767 to +32767 (one's complement)
            TRACESread = TRACES                             # How many traces, 1 or 2
            AUDIOsignal1 = []                               # Clear the AUDIOsignal1 array for trace 1
            AUDIOsignal2 = []                               # Clear the AUDIOsignal1 array for trace 1

            if TRACESread == 1:                             # Conversion routine for 1 trace
                AUDIOsignal1 = AUDIOsignals

            if TRACESread == 2:                             # Conversion routine for 2 traces
                n = 0
                while n < len(AUDIOsignals):
                    AUDIOsignal1.append(AUDIOsignals[n])
                    AUDIOsignal2.append(AUDIOsignals[n+1])
                    n = n + 2
                
            UpdateAll()                                     # Update Data, trace and screen

        # RUNstatus = 3: Stop
        # RUNstatus = 4: Stop and restart
        if (RUNstatus == 3) or (RUNstatus == 4):
            stream.stop_stream()
            stream.close()
            PA.terminate()
            if RUNstatus == 3:
                RUNstatus = 0                               # Status is stopped 
            if RUNstatus == 4:          
                RUNstatus = 1                               # Status is (re)start

            UpdateScreen()                                  # UpdateScreen() call


        # Update tasks and screens by TKinter 
        root.update_idletasks()
        root.update()                                       # update screens


def UpdateAll():        # Update Data, trace and screen
    CalculateData()     # Make the traces
    MakeTrace()         # Update the traces
    UpdateScreen()      # Update the screen 


def UpdateTrace():      # Update trace and screen
    MakeTrace()         # Update traces
    UpdateScreen()      # Update the screen


def UpdateScreen():     # Update screen with trace and text
    MakeScreen()        # Update the screen
    root.update()       # Activate updated screens    


def CalculateData():    # Calculate the trace data
    global AUDIOsignal1
    global AUDIOsignal2
    global T1line
    global T2line
    global Triggerline
    global X0L
    global Y0T
    global GRW
    global GRH
    global Ymin
    global Ymax
    global SHOWsamples
    global SCstart
    global TRACES
    global TRACESread
    global RUNstatus
    global ADsens1
    global ADsens2
    global CHvdiv1x
    global CH1probe
    global CH2probe
    global CH1div
    global CH2div
    global TIMEdiv1x
    global TIMEdiv
    global SAMPLErate
    global TRIGGERsample
    global TRIGGERlevel
    global LONGchunk
    global ADzero 

    
    # Set the TRACEsize variable
    TRACEsize = len(AUDIOsignal1)               # Set the trace length


    # Continue with finding the trigger sample and drawing the traces 
    if TRACEsize == 0:                          # If no trace, skip rest of this routine
         return() 


    # Zero offset correction routine for 1 trace of the AD converter if ADzero is True
    if ADzero == True and TRACESread == 1:
        AD1 = 0        

        t = int(0.1 * TRACEsize)                # skip first part of trace to avoid transients due to start of audio stream
        while t < TRACEsize:
            AD1 = AD1 + AUDIOsignal1[t]
            t = t + 1

        AD1 = int(AD1 / (0.9 * TRACEsize))      # 0.9 as first 0.1 part is skipped

        t = 0
        while t < TRACEsize:
            AUDIOsignal1[t] = AUDIOsignal1[t] -  AD1
            t = t + 1

    # Zero offset correction routine for 2 traces of the AD converter if ADzero is True
    if ADzero == True and TRACESread == 2:
        AD1 = 0
        AD2 = 0

        t = int(0.1 * TRACEsize)                # skip first part of trace to avoid transients due to start of audio stream
        while t < TRACEsize:
            AD1 = AD1 + AUDIOsignal1[t]
            AD2 = AD2 + AUDIOsignal2[t]
            t = t + 1

        AD1 = int(AD1 / (0.9 * TRACEsize))      # 0.9 as first 0.1 part is skipped
        AD2 = int(AD2 / (0.9 * TRACEsize))

        t = 0
        while t < TRACEsize:
            AUDIOsignal1[t] = AUDIOsignal1[t] -  AD1
            AUDIOsignal2[t] = AUDIOsignal2[t] -  AD2
            t = t + 1

        SCstart = 0                             # Set start postition to zero

 
def MakeTrace():    # Make the traces
    global AUDIOsignal1
    global AUDIOsignal2
    global T1line
    global T2line
    global Triggerline
    global X0L
    global Y0T
    global GRW
    global GRH
    global Ymin
    global Ymax
    global SHOWsamples
    global SCstart
    global TRACES
    global TRACESread
    global RUNstatus
    global ADsens1
    global ADsens2
    global CHvdiv1x
    global CH1probe
    global CH2probe
    global CH1div
    global CH2div
    global TIMEdiv1x
    global TIMEdiv
    global SAMPLErate
    global TRIGGERsample
    global TRIGGERlevel

     # Set the TRACEsize variable
    TRACEsize = len(AUDIOsignal1)               # Set the trace length

    # Continue with finding the trigger sample and drawing the traces 
    if TRACEsize == 0:                          # If no trace, skip rest of this routine
        T1line = []                             # Trace line channel 1
        T2line = []                             # Trace line channel 2
        return() 

    # Find trigger sample 
    TRIGGERsample = 0
        
    if LONGchunk == False:                          # For long sweeps no trigger
        TRIGGERlevel2 = int(0.9 * TRIGGERlevel)     # Hysteresis to avoid triggering at noise negative slope
        Nmax = int(TRACEsize / 3)
        n = TRIGGERsample
        while (AUDIOsignal1[int(n)] >= TRIGGERlevel2) and n < Nmax:
            n = n + 1
        while (AUDIOsignal1[int(n)] < TRIGGERlevel) and n < Nmax:
            n = n + 1
        if n < Nmax:
            TRIGGERsample = n
        

    # SCstart is set and/or corrected for in range
    SCmin = int(-1 * TRIGGERsample)
    SCmax = int(TRACEsize - TRIGGERsample - 20)
        
    if SCstart < SCmin:             # No reading before start of array
        SCstart = SCmin
    if SCstart  > SCmax:            # No reading after end of array
        SCstart = SCmax


    # Make Trace lines etc.
    if TRACES == 2:
        Yoffset = GRH / 4                               # offset when displaying 2 traces
    else:
        Yoffset = 0                                     # No offset if 1 trace

    Yconv1 = float(GRH/10) * 1000 / (ADsens1 * CHvdiv1x[CH1div])    # Conversion factors from audio samples to screen points
    Yconv2 = float(GRH/10) * 1000 / (ADsens2 * CHvdiv1x[CH2div])    

    c1 = GRH / 2 + Y0T - Yoffset    # fixed correction channel 1
    c2 = GRH / 2 + Y0T + Yoffset    # fixed correction channel 2

    SHOWsamples = SAMPLErate * 10 * TIMEdiv1x[TIMEdiv] / 1000 

    T1line = []                     # Trace line channel 1
    T2line = []                     # Trace line channel 2
    t = SCstart + TRIGGERsample     # t = Start sample in audio trace
    x = 0                           # Horizontal screen pixel

    if (SHOWsamples <= GRW):
        Xstep = GRW / SHOWsamples
        Tstep = 1
        x1 = 0                      # x position of trace line
        y1 = 0.0                    # y position of trace 1 line
   
        while (x <= GRW):
            if (t < TRACEsize):
                x1 = x + X0L
                y1 = int(c1 - Yconv1 * float(AUDIOsignal1[int(t)]))

                if (y1 < Ymin):
                    y1 = Ymin
                if (y1 > Ymax):
                    y1 = Ymax
                T1line.append(int(x1))
                T1line.append(int(y1))        

                if (TRACESread == 2 and TRACES == 2):
                    y1 = int(c2 - Yconv2 * float(AUDIOsignal2[int(t)]))

                    if (y1 < Ymin):
                        y1 = Ymin
                    if (y1 > Ymax):
                        y1 = Ymax
                    T2line.append(int(x1))
                    T2line.append(int(y1))        

            t = t + Tstep
            x = x + Xstep

    if (SHOWsamples > GRW):
        Xstep = 1
        Tstep = SHOWsamples / GRW
        x1 = 0                          # x position of trace line
        ylo = 0.0                       # ymin position of trace 1 line
        yhi = 0.0                       # ymax position of trace 1 line

        t = SCstart + TRIGGERsample     # t = Start sample in audio trace
        x = 0                           # Horizontal screen pixel
    
        while (x <= GRW):
            if (t < TRACEsize):
                x1 = x + X0L

                ylo = float(AUDIOsignal1[int(t)])
                yhi = ylo

                n = t
                while n < (t + Tstep) and n < TRACEsize:
                    v = float(AUDIOsignal1[int(n)])
                    if v < ylo:
                        ylo = v
                    if v > yhi:
                        yhi = v

                    n = n + 1   
                
                ylo = int(c1 - Yconv1 * ylo)
                yhi = int(c1 - Yconv1 * yhi)
                if (ylo < Ymin):
                    ylo = Ymin
                if (ylo > Ymax):
                    ylo = Ymax

                if (yhi < Ymin):
                    yhi = Ymin
                if (yhi > Ymax):
                    yhi = Ymax
                T1line.append(int(x1))
                T1line.append(int(ylo))        
                T1line.append(int(x1))
                T1line.append(int(yhi))        

                if (TRACESread == 2 and TRACES == 2):
                    ylo = float(AUDIOsignal2[int(t)])
                    yhi = ylo

                    n = t
                    while n < (t + Tstep) and n < TRACEsize:
                        v = float(AUDIOsignal2[int(n)])
                        if v < ylo:
                            ylo = v
                        if v > yhi:
                            yhi = v

                        n = n + 1   
                
                    ylo = int(c2 - Yconv2 * ylo)
                    yhi = int(c2 - Yconv2 * yhi)
                    if (ylo < Ymin):
                        ylo = Ymin
                    if (ylo > Ymax):
                        ylo = Ymax

                    if (yhi < Ymin):
                        yhi = Ymin
                    if (yhi > Ymax):
                        yhi = Ymax
                    T2line.append(int(x1))
                    T2line.append(int(ylo))        
                    T2line.append(int(x1))
                    T2line.append(int(yhi))
                    
            t = t + Tstep
            x = x + Xstep

    # Make trigger line
    Triggerline = []                # Triggerline

    x1 = X0L
    y1 = int(c1 - Yconv1 * float(TRIGGERlevel))

    if (y1 < Ymin):
        y1 = Ymin
    if (y1 > Ymax):
        y1 = Ymax
    Triggerline.append(int(X0L-5))
    Triggerline.append(int(y1))        
    Triggerline.append(int(X0L+5))
    Triggerline.append(int(y1))        


def MakeScreen():     # Update the screen with traces and text
    global AUDIOsignal1
    global AUDIOsignal2
    global T1line
    global T2line
    global Triggerline
    global X0L          # Left top X value
    global Y0T          # Left top Y value
    global GRW          # Screenwidth
    global GRH          # Screenheight
    global Ymin
    global Ymax
    global SHOWsamples  # Number of samples on the screen
    global SCstart
    global TRACES
    global TRACESread   # Number of traces 1 or 2
    global RUNstatus    # 0 stopped, 1 start, 2 running, 3 stop now, 4 stop and restart
    global ADsens1      # Sensitivity of AD converter CH1 1 V = 1000 levels
    global ADsens2      # Sensitivity of AD converter CH2 1 V = 1000 levels
    global CHvdiv1x     # Sensitivity list in mv/div
    global CH1probe     # Probe attenuation factor 1x, 10x or 0.1 x of channel 1
    global CH2probe     # Probe attenuation factor 1x, 10x or 0.1 x of channel 2
    global CH1div       # Index value of CHvdiv1x for channel 1
    global CH2div       # Index value of CHvdiv1x for channel 2
    global TIMEdiv1x    # Array with time / div values in ms
    global TIMEdiv      # Index in array
    global SAMPLErate
    global TRIGGERsample
    global TRIGGERlevel
    global LONGchunk    # If longchunk is used for longsweep
    global ADzero       # Corrects the AD converter by taking the average of the Trace and offset it to zero.
    global COLORgrid    # The colors
    global COLORzeroline
    global COLORtrace1
    global COLORtrace2
    global COLORtext
    global COLORtrigger
    global CANVASwidth
    global CANVASheight
    global TRACErefresh
    global SCREENrefresh

    # Delete all items on the screen
    de = ca.find_enclosed ( 0, 0, CANVASwidth+1000, CANVASheight+1000)    
    for n in de: 
        ca.delete(n)

    # Draw horizontal grid lines
    i = 0
    x1 = X0L
    x2 = X0L + GRW
    while (i < 11):
        y = Y0T + i * GRH/10
        Dline = [x1,y,x2,y]
        if (i == 5) and (TRACES == 1):
            ca.create_line(Dline, fill=COLORzeroline)   # Blue horizontal line for 1 trace
        else:
            ca.create_line(Dline, fill=COLORgrid)            
        i = i + 1

    if TRACES == 2:
        Yoffset = GRH / 4                               # offset when displaying 2 traces
        y = Y0T + Yoffset
        Dline = [x1,y,x2,y]
        ca.create_line(Dline, fill=COLORzeroline)       # Blue horizontal line 1 for 2 traces

        y = Y0T + 3 * Yoffset
        Dline = [x1,y,x2,y]
        ca.create_line(Dline, fill=COLORzeroline)       # Blue horizontal line 1 for 2 traces
    else:
        Yoffset = 0                                     # No offset if 1 trace

    # Draw vertical grid lines
    i = 0
    y1 = Y0T
    y2 = Y0T + GRH
    while (i < 11):
        x = X0L + i * GRW/10
        Dline = [x,y1,x,y2]
        ca.create_line(Dline, fill=COLORgrid)
        i = i + 1

    # Write the trigger line if available
    if len(Triggerline) > 2:                                # Avoid writing lines with 1 coordinate
        ca.create_line(Triggerline, fill=COLORtrigger)

    # Write the traces if available
    if len(T1line) > 4:                                     # Avoid writing lines with 1 coordinate    
        ca.create_line(T1line, fill=COLORtrace1)            # Write the trace 1
    if TRACESread == 2 and TRACES == 2 and len(T2line) > 4: # Write the trace 2 if active
        ca.create_line(T2line, fill=COLORtrace2)            # and avoid writing lines with 1 coordinate

    # General information on top of the grid
    if ADzero == True:
        txt = "DC offset correction on "
    else:
        txt = "DC offset correction off"

    txt = txt + "   Sample rate: " + str(SAMPLErate) + "    "

    x = X0L
    y = 12
    idTXT = ca.create_text (x, y, text=txt, anchor=W, fill=COLORtext)

    # Time sweep information and view at information
    vx = TIMEdiv1x[TIMEdiv]
    if vx >= 1000:
        txt = str(int(vx/1000)) + " s/div"
    if vx < 1000 and vx >= 1:
        txt = str(int(vx)) + " ms/div"
    if vx < 1:
        txt ="0." + str(int(vx * 10)) + " ms/div"

    txt = txt + "     "
    vt = 1000 * float(SCstart) / SAMPLErate    

    if vt < 0:
        txt = txt + "View at -"
        vt = vt * -1
    else:
        txt = txt + "View at +"

    vt = vt + 0.05        # Prevent decimal errors (0.9999999 etc)
    vt1 = int(vt)
    vt2 = int(10 * (vt - int(vt)))
    txt = txt + str(vt1) + "." + str(vt2) + " ms     " 

    x = X0L
    y = Y0T+GRH+12
    idTXT = ca.create_text (x, y, text=txt, anchor=W, fill=COLORtext)

    # Channel 1 information
    if CH1probe == 0.1:
        txt = "0.1x CH1: "
                           
    if CH1probe == 1:
        txt = "1x CH1: "
        
    if CH1probe == 10:
        txt = "10x CH1: "

    vy = CH1probe * CHvdiv1x[CH1div]
    if vy >= 1000:
        txt = txt + str(int(vy/1000)) + " V/div"
    if vy < 1000 and vy >= 1:
        txt = txt + str(int(vy)) + " mV/div"
    if vy < 1:
        txt = txt + "0." + str(int(vy * 10)) + " mV/div"

    x = X0L
    y = Y0T+GRH+24
    idTXT = ca.create_text (x, y, text=txt, anchor=W, fill=COLORtext)

    # Channel 2 information
    if TRACESread == 2 and TRACES == 2:
        if CH2probe == 0.1:
            txt = "0.1x CH2: "
                           
        if CH2probe == 1:
            txt = "1x CH2: "
        
        if CH2probe == 10:
            txt = "10x CH2: "

        vy = CH2probe * CHvdiv1x[CH2div]
        if vy >= 1000:
            txt = txt + str(int(vy/1000)) + " V/div"
        if vy < 1000 and vy >= 1:
            txt = txt + str(int(vy)) + " mV/div"
        if vy < 1:
            txt = txt + "0." + str(int(vy * 10)) + " mV/div"

        x = X0L
        y = Y0T+GRH+36
        idTXT = ca.create_text (x, y, text=txt, anchor=W, fill=COLORtext)

    # Sweep information
    if LONGsweep == False and LONGchunk == False:
        txt = "Running"
        if (RUNstatus == 0) or (RUNstatus == 3):
            txt = "Stopped"

    if LONGsweep == True or LONGchunk == True:
        txt = "Running long sweep, wait"
        if (RUNstatus == 0) or (RUNstatus == 3):
            txt = "Stopped long sweep, press Start"
    
    x = X0L
    y = Y0T+GRH+48
    idTXT = ca.create_text (x, y, text=txt, anchor=W, fill=COLORtext)
    

def SELECTaudiodevice():        # Select an audio device
    global AUDIOdevin

    PA = pyaudio.PyAudio()
    ndev = PA.get_device_count()

    n = 0
    ai = ""
    ao = ""
    while n < ndev:
        s = PA.get_device_info_by_index(n)
        # print(n, s)
        if s['maxInputChannels'] > 0:
            ai = ai + str(s['index']) + ": " + s['name'] + "\n"
        n = n + 1
    PA.terminate()

    AUDIOdevin = None
    
    s = simpledialog.askstring("Device","Select audio INPUT device:\nPress Cancel for Windows Default\n\n" + ai + "\n\nNumber: ")
    if (s != None):             # If Cancel pressed, then None
        try:                    # Error if for example no numeric characters or OK pressed without input (s = "")
            v = int(s)
        except:
            s = "error"

        if s != "error":
            if v < 0 or v > ndev:
                v = 0
            AUDIOdevin = v


# ================ Make Screen ==========================

root=Tk()
root.title("OscilloscopeV02a.py(w) (13-10-2018): Audio Oscilloscope")

root.minsize(100, 100)

frame1 = Frame(root, background=COLORframes, borderwidth=5, relief=RIDGE)
frame1.pack(side=TOP, expand=1, fill=X)

frame2 = Frame(root, background="black", borderwidth=5, relief=RIDGE)
frame2.pack(side=TOP, expand=1, fill=X)

frame3 = Frame(root, background=COLORframes, borderwidth=5, relief=RIDGE)
frame3.pack(side=TOP, expand=1, fill=X)

ca = Canvas(frame2, width=CANVASwidth, height=CANVASheight, background=COLORcanvas)
ca.pack(side=TOP)

b = Button(frame1, text="-TrigLevel", width=Buttonwidth1, command=BTriglevel1)
b.pack(side=LEFT, padx=5, pady=5)

b = Button(frame1, text="+TrigLevel", width=Buttonwidth1, command=BTriglevel2)
b.pack(side=LEFT, padx=5, pady=5)

b = Button(frame1, text="1/2 Channels", width=Buttonwidth1, command=BTraces)
b.pack(side=LEFT, padx=5, pady=5)

b = Button(frame1, text="Setup", width=Buttonwidth1, command=BSetup)
b.pack(side=RIGHT, padx=5, pady=5)

b = Button(frame3, text="Start", width=Buttonwidth2, command=BStart)
b.pack(side=LEFT, padx=5, pady=5)

b = Button(frame3, text="Stop", width=Buttonwidth2, command=BStop)
b.pack(side=LEFT, padx=5, pady=5)

b = Button(frame3, text="-Time", width=Buttonwidth2, command=BTime1)
b.pack(side=LEFT, padx=5, pady=5)

b = Button(frame3, text="+Time", width=Buttonwidth2, command=BTime2)
b.pack(side=LEFT, padx=5, pady=5)

b = Button(frame3, text="-CH1", width=Buttonwidth2, command=BCH1level1)
b.pack(side=LEFT, padx=5, pady=5)

b = Button(frame3, text="+CH1", width=Buttonwidth2, command=BCH1level2)
b.pack(side=LEFT, padx=5, pady=5)

b = Button(frame3, text="-CH2", width=Buttonwidth2, command=BCH2level1)
b.pack(side=LEFT, padx=5, pady=5)

b = Button(frame3, text="+CH2", width=Buttonwidth2, command=BCH2level2)
b.pack(side=LEFT, padx=5, pady=5)

b = Button(frame3, text="Probe", width=Buttonwidth2, command=Bprobe)
b.pack(side=RIGHT, padx=5, pady=5)

b = Button(frame3, text="+View", width=Buttonwidth2, command=BView2)
b.pack(side=RIGHT, padx=5, pady=5)

b = Button(frame3, text="-View", width=Buttonwidth2, command=BView1)
b.pack(side=RIGHT, padx=5, pady=5)


# ================ Call main routine ===============================
root.update()               # Activate updated screens
SELECTaudiodevice()
AUDIOin()
 


