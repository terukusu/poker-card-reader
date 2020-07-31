# poker-card-reader
This is a card reader for certain types of online poker(Texas Hold'em).  
This tools is only for Mac.  
  
Looks like this.   
<img width="80%" src="https://raw.githubusercontent.com/terukusu/poker-card-reader/images/images/screenshot_card_read.png" />

## How it works
1. Capture the window of poker table with PyObjc.
1. Detect suit and number of cards with OpenCV.
  
That's all :-)  

## How to use
**pre-requist**
* Mac
* python 3.6+
  
**prepare venv**
```
$ python3 -m venv venv
$ . venv/bin/activate
```
  
**install requirements**
```
$ pip install -r requirements.txt
```

**run**
```
$ watch -n 1 python main.py
(after that, boot the certain online poker client and enjoy!)
```
* You can isntall "watch" command using [homebrew](https://brew.sh/).
* Please try to resize window if card is not detected properly.
