# binary reader import
import os
from time import time
from apread.binaryReader import BinaryReader

# plotting
import matplotlib.pyplot as plt
import plotly.express as px
import scipy.signal as sig

# serialization
import json

# progress
from tqdm import tqdm
from apread.loader import Loader
import numpy as np
# filtering
from scipy.signal import lfilter

# typing
from typing import List

class Channel:
    """
    Holds data of a Catman Channel.    

    Information:
            APReader uses the Channel-Lengths to connect Channels together.
            Say there are two Channels with Length 100, then one of those will have "Time" in its name.
            The other one then gets a reference to the "time" one.
            
            If there is more than one channel having the same amount of entries, every channel will 
            get the same reference to the time channel.
    """        
    # data: List[float]
    verbose: bool
    # Defines if data should be filtered.
    filterData: bool

    def __init__(self, reader: BinaryReader, fileName='unknown', verbose=False, filterData=False, fastload=True):
        """
        Creates the Channel.

        Uses a reader (BinaryReader) to read the data from the file accessed by "APReader.__init__".
        """
        self.fastload = fastload
        # defines, if the apreader should output verbose debug messages
        self.verbose = verbose
        # defines, wether read data should be filtered
        self.filterData = filterData

        # referenced time channel (dummy, since this may stay None)
        self.Time = None
        self.isTime = False
        # save the reader for later use
        self.reader = reader

        # get index of channel
        self.num = reader.read_int16()
        # get length of channel
        self.length = reader.read_int32()
        # get name of channel
        self.Name = reader.read_string(reader.read_int16())

        # the original file name of the group
        self.fileName = os.path.splitext(os.path.basename(fileName))[0]
        tName = self.Name.replace(' ',"_")  # temporary name
        self.fullName = f"{fileName}.{tName}"

        # retrieve unit of channel                
        
        self.unit = reader.read_string(reader.read_int16())
        
        # get comment of channel                
        self.comment = reader.read_string(reader.read_int16())

        # 0: numeric, 1: string, 2: binary object
        self.format  = reader.read_int16()
        # get format of channel (8: numeric, >8: string)
        self.dw = reader.read_int16()
        # time of reading
        self.time = reader.read_double()
        # extended channel header
        self.nHdrBytes = reader.read_int32()
        self.extHeader = self.readExtHeader(reader)
        
        precDict = {0:8, 1:4, 2:2} # key: Attribute "Exportformat", value: precision in bytes
        try:
            self.precision = precDict[self.extHeader['ExportFormat']]
        except KeyError:
            print('Unexpected value of attribute "ExportFormat" in the extended header of channel {}. Assuming double precision.'.format(self.Name))
            self.precision = 8

        # linearization mode
        self.lmode = reader.read_char()
        # user scale
        self.scale = reader.read_char()
        # unknown points
        self.npoi = reader.read_byte()
        # readaway
        for i in range(self.npoi):
            reader.read_double()

        # thermo type
        reader.read_int16()

        # readaway
        self.formula = reader.read_string(reader.read_int16())
        self.sensorInfo = reader.read_string(reader.read_int32())

        # flag to indicate that everything is fine
        self.broken = False

    def readExtHeader(self, rdr: BinaryReader):
        """
        Reads the extended header of this Channel.

        NOTE: The catman binary files use byte padding, which means that all
        values are stored at byte addresses which are integer multiples of their
        width in bytes (i.e. doubles are stored on addresses divisible by eight,
        floats on addresses divisible by four etc.)
        
        See the link below for more info:        
        https://stackoverflow.com/questions/4306186/structure-padding-and-packing
        
        For this reason, I've added three bytes of padding before the attribute
        'NominalRange', which is a float.
            
        """
        pos0 = rdr.tell() # In general not a multiple of eight, which is unexpected!

        exthdr = {}
        exthdr['T0'] = rdr.read_double() # (pos0+) 8
        exthdr['dt'] = rdr.read_double() # 16
        exthdr['SensorType'] = rdr.read_int16() # 18
        exthdr['SupplyVoltage'] = rdr.read_int16() # 20
        
        exthdr['FiltChar'] = rdr.read_int16() # 22
        exthdr['FiltFreq'] = rdr.read_int16() # 24
        exthdr['TareVal'] = rdr.read_float() # 28
        exthdr['ZeroVal'] = rdr.read_float() # 32   
        exthdr['MeasRange'] = rdr.read_float() # 36
        exthdr['InChar'] = [rdr.read_float() for i in range(4)] # 40, 44, 48, 52
        
        exthdr['SerNo'] = rdr.read_string(32) # 84
        exthdr['PhysUnit'] = rdr.read_string(8) # 92
        exthdr['NativeUnit'] = rdr.read_string(8) # 100
        
        exthdr['Slot'] = rdr.read_int16() # 102
        exthdr['SubSlot'] = rdr.read_int16() # 104
        exthdr['AmpType'] = rdr.read_int16() # 106
        exthdr['APType'] = rdr.read_int16() # 108
        exthdr['kFactor'] = rdr.read_float() # 112
        exthdr['bFactor'] = rdr.read_float() # 116
        
        exthdr['MeasSig'] = rdr.read_int16() # 118
        exthdr['AmpInput'] = rdr.read_int16() # 120
        exthdr['HPFilt'] = rdr.read_int16() # 122
        exthdr['OLImportInfo'] = rdr.read_byte() # 123
        exthdr['ScaleType'] = rdr.read_byte() # 124
        exthdr['SoftwareTareVal'] = rdr.read_float() # 128        
        exthdr['WriteProtected'] = rdr.read_byte() # 129
        padding = rdr.read_string(3) # 132
        
        exthdr['NominalRange'] = rdr.read_float() # 136 
        exthdr['CLCFactor'] = rdr.read_float() # 140
        exthdr['ExportFormat'] = rdr.read_byte() # 141
        reserve = rdr.read_string(7) # 148
        # reserve = rdr.read_string(10)        
        posN = rdr.tell()
        
        if (posN-pos0) != self.nHdrBytes:
            print("""
                  WARNING:
                  The number of bytes read in the extended header of the channel
                  '{}'
                  doesn't match its declared length.
                  This probably means that the hardcoded format definition in the method
                  'Channel.readExtHeader' is no longer valid and must be revised.
                  Leaving the extended header as-is and resetting the read position of
                  the binary reader. Assuming double precision for the data.
                  """.format(self.Name))
            rdr.seek(pos0 + self.nHdrBytes)
            exthdr['ExportFormat'] = 0
        
        return exthdr

    def readData(self):
        """
        Reads the data of this Channel.

        IMPORTANT
            The stream offset has to be set before calling this function!
        """
        # if something was wrong previously, nothing will happen here
        if self.broken:
            return
        
        if self.fastload:
            # The data is stored channelwise. We therefore only need to pass pointers to the first and last byte.
            if self.precision == 8 or self.precision == 4:
                self.data = np.fromfile(self.reader.buf, dtype=np.dtype('f{}'.format(self.precision)), count=self.length)
            elif self.precision == 2:
                MinValue = self.reader.read_double()
                MaxValue = self.reader.read_double()
                sf = (MaxValue - MinValue)/32767 # scale factor
                self.data = np.fromfile(self.reader.buf, dtype=np.dtype('u2'), count=self.length)*sf + MinValue
        else:
            # initialize data
            self.data = []

            # read all channel data            
            if self.precision == 8:
                for i in tqdm(range(self.length), leave=False):
                    self.data.append(self.reader.read_double())
            elif self.precision == 4:
                for i in tqdm(range(self.length), leave=False):
                    self.data.append(self.reader.read_float())
            elif self.precision == 2:                
                MinValue = self.reader.read_double()
                MaxValue = self.reader.read_double()
                sf = (MaxValue - MinValue)/32767 # scale factor
                
                for i in tqdm(range(self.length), leave=False):
                    self.data.append(self.reader.read_int16()*sf + MinValue)

        # filter data
        if self.filterData:
            with Loader('Filtering data...'):
                self.data = self.filter()

    def filter(self, mode='lfilt'):
        if mode == 'lfilt':
            n = 50  # the larger n is, the smoother curve will be
            b = [1.0 / n] * n
            a = 1
            return lfilter(b,a,self.data)


    def plot(self, mode = 'ply', governed = False):
        """
        Plot the channel over its connected time-channel.

        mode:
            'ply'   Plotly,
            'mat'   matplotlib

        governed:
            States wether the call to this function will handle figures and handles.
            If False, a single figure will be shown.
        """
        # cant plot time over time
        if self.isTime:
            if self.verbose:
                print("\t[ APREAD/PLOT ] Channel is time. Not plotting.")
            return

        if self.Time is None:
            print("\t[ APREAD/PLOT ] Channel does not have time data. Not plotting.")
            return

        
        if self.verbose:
            print(f'\t[ APREAD/PLOT ] Filtering plot for {self.Name}')
        
        # filter data
        datay = sig.wiener(self.data)

        if self.verbose:
            print(f'\t[ APREAD/PLOT ] Plotting {self.Name}')
        if 'ply' in mode:
            fig = px.line(x = self.Time.data, y = datay, title = f'{self.Name}')
            if not governed:
                fig.show()
            else:
                print('Cant handle governed mode and plotly.')
                return
        elif 'mat' in mode:
            if not governed:
                fig = plt.figure(self.Name)
                plt.xlabel('Time [s]')
                plt.ylabel(self.unit)

            plt.plot(self.Time.data, datay, label=self.Name)

            if not governed:
                plt.title(self.Name)
                plt.draw()
                plt.legend()        
                plt.show()

    def __str__(self):
        """
        Default conversion to string.
        """
        print(self.Name)
        for d in self.data:
            print(d)

    def __getitem__(self, key) -> float:
        """Return the item at index key.

        Args:
            key (int): index

        Returns:
            double: self.data[key]
        """
        return self.data[key]

    def save(self, mode, path):
        """Save channel as text.

        Args:
            mode (str): 'csv' or 'json'
            path (str): the destination directory(!) path
        """
        
        if self.isTime:
            if self.verbose: print('\tChannel cant be saved since it is a Time-Channel')
            return

        if self.length == 0 :
            if self.verbose: print('\tChannel has no data and cant be saved.')
            return

        # ensure destination exists
        dest = os.path.join(path, self.fullName + '.json')

        # check if the path exists and create if necessary
        if not os.path.exists(path):
            os.makedirs(path)

        content = self.getas(mode)
        
        with open(dest, 'w') as file:
            file.write(content)
            

    def getas(self, mode):
        """Save channel as text.

        Args:
            mode (str): 'csv' or 'json'
            path (str): the destination directory(!) path
        """

        if self.isTime:
            return

        if self.length == 0:
            return

        # get total length
        length = self.length

        content = ""
        # check, which mode to use as save
        if mode == 'csv':
            # write content to file
            for i in tqdm(range(length), desc=f'Create CSV: {self.Name}'):
                content += (f'{self.Time.data[i] if self.Time is not None else ""}\t{self.data[i]}\n')
            if self.verbose:
                print(f'\t☑ [ {self.fullName} → CSV ].')

        elif mode == 'json':
            # write content to file
            
            data = {}
            if self.Time is not None: data['X'] = self.Time.data
            data['Y'] = self.data
            
            # output json
            with Loader(f'Create JSON: {self.Name}', end=f'\t☑ [ {self.fullName} → JSON ]' if self.verbose else ""):
                content = json.dumps(data, indent=4)

        else:
            raise Exception(f"Unknown mode: {mode}")        

        return content

class Group:
    """
    Groups channels together.

    Helps calling plot functions..
    """
    # all (unsorted) channels in this group
    Channels: List[Channel]
    # Name of the time channel of this group
    Name: str

    # the time-channel
    ChannelX: Channel
    # all other data-channels
    ChannelsY: List[Channel]

    # the data time interval with a fitting unit
    intervalstr: str
    # the data time interval in milliseconds
    interval: float
    # frequency of the corresponding time
    frequency: float

    # the file this group is located in
    fileName: str
    # fully qualifying name
    fullName: str



    def __init__(self, channels: List[Channel], fileName='unknown', verbose=False):
        """Create group of channels.

        Args:
            channels (list[Channel]): The channels this group is based on.        
        """
        self.verbose = verbose
        # save all channels
        self.Channels = channels
        # get first channel which is marked as "isTime"
        timeC = next((x for x in channels if x.isTime), None)
        self.ChannelX = timeC

        if timeC is None:
            # if no time found, group cant be shown
            if self.verbose:
                print('\t[ APREAD/WARNING ] Group does not have a time-channel. Skipping...')
        elif timeC is not None:
            # get name of time channel
            self.Name = timeC.Name

        # the original file name of the group
        self.fileName = os.path.splitext(os.path.basename(fileName))[0]
        tName = self.Name.replace(' ',"_")  # temporary name
        self.fullName = f"{fileName}.{tName}"


        # get all other channels
        self.ChannelsY = []
        for chan in channels:
            if not chan.isTime:
                self.ChannelsY.append(chan)

        # determine frequency and time delta unit
        unit = 's'
        fac = 1
        if timeC.data[1] < 1:
            unit = 'ms'
            fac = 1e3
        if timeC.data[1] < 1e-3:
            unit = 'ns'
            fac = 1e6
        if timeC.data[1] < 1e-6:
            unit = 'μs'
            fac = 1e9

        self.intervalstr = f"{timeC.data[1]*fac:.3f}{unit}"
        self.interval = timeC[1]/1e3
        self.frequency = 1/timeC.data[1]

    def plot(self, governed=False):
        """Plots this group of channels

        Args:
            governed (bool, optional): States wether this plot-function is called from another plot-function. When nesting plot functions, the base function has to call plt.show. Defaults to False.
        """
        if not governed:
            fig = plt.figure(self.Name)

        for channel in self.ChannelsY:
            channel.plot(mode='mat', governed=True)

        if not governed:
            plt.title(self.Name)
            plt.draw()
            plt.legend()
            plt.show()
        

    def __getitem__(self, key):
        """Return the time and all y-channels at index.

        Args:
            key (int): index

        Returns:
            double: self.data[key]
        """
        return (self.ChannelX[key], [chan[key] for chan in self.ChannelsY])

    def save(self, mode, path):
        """Save group as text.

        Args:
            mode (str): 'csv' or 'json'
            path (str): the destination directory(!) path
        """
        
        # ensure destination exists
        dest = os.path.join(path, self.fullName + f'.{mode}')

        # check if path present
        if not os.path.exists(path):
            os.makedirs(path)

        # if there only is one channel, save only the channel
        if len(self.ChannelsY) == 1:
            self.ChannelsY[0].save(mode, path)
            return

        # otherwise get the formatted group
        #  this will always have the time channel plus all y-channels
        content = self.getas(mode)
        # write the content
        with open(dest, 'w') as file:
            file.write(content)
        

    def getas(self, mode):
        """Format group as text.

        Args:
            mode (str): 'csv' or 'json'
            path (str): the destination directory(!) path

        Returns:
            A formatted string representing this group in the specified mode.
        """
        # get length of y-channels
        length_x = len(self.ChannelsY)
        # get total length
        length = len(self.ChannelX.data) if self.ChannelX is not None else (len(self.ChannelsY[0]) if length_x > 0 else 0)

        # start with empty content
        content = ""

        # check, which mode to use as save
        if mode == 'csv':
            # put every time-value-pair as row
            for i in tqdm(range(length), desc=f'Create CSV: {self.Name}'):
                # start with time-channel
                content += (f'{self.ChannelX.data[i]}')

                # use \t as delimiter
                for j in range(length_x):
                    content += (f'\t{self.ChannelsY[j].data[i]}')

                content += ('\n')

            if self.verbose:
                print(f'\t☑ [ {self.fullName} → CSV ] ✓.')

        elif mode == 'json':
            # write content to file

            # create dummy dictionary to save as json
            data = {}
            if self.ChannelX is not None:
                data['X'] = self.ChannelX.data
            # add y-data to dict
            for j in range(length_x):
                data[f'Y{j}'] = self.ChannelsY[j].data
            
            # output json
            with Loader(f'Create JSON: {self.Name}', end=f'\t☑ [ {self.fullName} → JSON ]' if self.verbose else ""):
                # create json formatted string
                content = json.dumps(data, indent=4)

        else:
            raise Exception(f"Unknown mode: {mode}")        

        return content
