
[![PyPi Upload](https://github.com/leonbohmann/APReader/actions/workflows/python-publish.yml/badge.svg)](https://github.com/leonbohmann/APReader/actions/workflows/python-publish.yml)
![pyPI - Version](https://img.shields.io/pypi/v/apread?label=package%20version)
![PyPI - Downloads](https://img.shields.io/pypi/dm/apread?color=green&label=PyPi%20Downloads&style=plastic)

# **apread** (Catman AP Reader)
> Read binary files produced from catmanAP projects directly into python.

CatmanAP procudes .bin files after each measurement. While it is possible to export as a different format (i.e. txt or asc) it's not efficient because one has to change the export format after every measurement. Here comes the treat: Just export as binary and use this package to work with binary files directly.

After reading all channels from the binary file, the channels are analyzed and every measure-channel will receive a reference to a time channel, depending on the amount of entries in the channels and the fact, that the time-channel has to contain "time" or "zeit" in its name. What that means is, that a channel with x entries and the name "time - 1" will be regarded as the time-channel of any other channel with x Data Entries.

Here is an example plot, generated directly from a binary file:
![apread_demo_out_1](https://user-images.githubusercontent.com/13386367/118563304-9dffba80-b76e-11eb-8730-c982c2ece7db.png)

## Installation

Anywhere with python:

```sh
pip install apread
```


## Usage

Lets say you produced a file called `measurements.bin` and you put it in the directory of your python script.

```python
from apread import APReader

reader = APReader('measurements.bin')
``` 

### Print channels
It's that simple. The `APReader`-Initialization may take some time depending on how large your .bin-File is. Afterwards you can access the `Channels` by accessing the `APReader.Channels` Member. A `Channel` implements `__str__` so you can just call `print(...)` on them. **Be careful** though, since this will print every value in the channel to the console.

```python
for channel in reader.Channels:
    print(channel)
``` 

### Plot Channels/Groups
Another possibility is to call `Channel.plot()`. This will create a plot of the channel. Since Version *1.0.12* you can also call `.plot()` on the newly introduced `reader.Groups`.
```python
for channel in reader.Channels:
    channel.plot()
``` 

### Save Channels/Groups
Use `save(mode, path)` to save a channel or group into a directory. The resulting file name will be the origin filename plus the groups or channels name. For ease of use you can call `reader.save(mode)` which is the equivalent to call `save` on every channel and group.
```python
for group in reader.Groups:
    # plot the group (plots time and every channel on the y-axis)
    group.plot()
    # saves the group into csv-format (delimiter is \t) 
    # time  y1  y2
    group.save(mode='csv')

    # saves the group into json-format
    # dictionary of data: 
    #   ['X'] : time
    #   ['Yn'] : y-Channel (where n is index)
    group.save(mode='json')

``` 
with the equivalent:
```python
reader.save(mode='json')
``` 

## Examples
Although not being a full example you can have a look into `testing.py` to get a glimpse of how to create a script using `apread`.


## Release History
### **Version 1.0.22**
* Fixed an issue with groups where time channels are not recognized
  *  now, user is prompted, when suspected time channel is found
  *  plotting is not possible when there is no time-channel found
  *  save groups and channels even when there is no time channel
### Version 1.0.21
* Updated serialisation-procedures to always encode in `UTF-8`
### Version 1.0.20
* Switched to explicit type hinting with `typing` package (compatibility issues with python <3.9.x)  
### Version 1.0.15/16
* Fixed an issue with saving and non-existent directories
* Added `getas` to generate formatted string without saving
### Version 1.0.14
* Output file-names updated
### Version 1.0.12/13
* Group channels with their time-channel into "groups"
* Multiple plot modes:
    * Whole file
    * Channel/Group only
* Output data
    * json
    * csv

### *Version 1.0.11*
* Progressbars indicate read-progress of files
* Multiple plot modes

### *Version 1.0.0*
* Convert catman files to channels

## Meta

Leon Bohmann – mail@leonbohmann.de

Distributed under the MIT license. See ``LICENSE`` for more information.

[https://github.com/leonbohmann/apreader](https://github.com/leonbohmann/apreader)
