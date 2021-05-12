[![PyPi Upload](https://github.com/leonbohmann/APReader/actions/workflows/python-publish.yml/badge.svg)](https://github.com/leonbohmann/APReader/actions/workflows/python-publish.yml)

# **apread** (Catman AP Reader)
> Read binary files produced from catmanAP projects directly into python.

CatmanAP procudes .bin files after each measurement. While it is possible to export as a different format (i.e. txt or asc) it's not efficient because one has to change the export format after every measurement. Here comes the treat: Just export as binary and use this package to work with binary files directly.

After reading all channels from the binary file, the channels are analyzed and every measure-channel will receive a reference to a time channel, depending on the amount of entries in the channels and the fact, that the time-channel has to contain "time" or "zeit" in its name. What that means is, that a channel with x entries and the name "time - 1" will be regarded as the time-channel of any other channel with x Data Entries.

## Installation

Anywhere with python:

```sh
pip install apread
```


## Usage example

Lets say you produced a file called `measurements.bin` and you put it in the directory of your python script.

```python
from apread import APReader

reader = APReader('measurements.bin')
``` 

It's that simple. The `APReader`-Initialization may take some time depending on how large your .bin-File is. Afterwards you can access the `Channels` by accessing the `APReader.Channels` Member. A `Channel` implements `__str__` so you can just call `print(...)` on them. **Be careful** though, since this will print every value in the channel to the console.

```python
for channel in reader.Channels:
    print(channel)
``` 

Another possibility is to call `Channel.plot()`. This will create a plot of the channel.
```python
for channel in reader.Channels:
    channel.plot()
``` 


## Release History

* Version 1.0.11
    * Progressbars indicate read-progress of files
    * Multiple plot modes

* Version 1.0.0
    * Convert catman files to channels

## Meta

Leon Bohmann – info@leonbohmann.de

Distributed under the MIT license. See ``LICENSE`` for more information.

[https://github.com/leonbohmann/apreader](https://github.com/leonbohmann/apreader)
