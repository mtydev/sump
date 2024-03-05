# SUMP
## What is SUMP?
Sump is a tool for finding "hard to get" items from polish version of olx or otomoto. Although OLX provides kind of mechanism like this tool does, it dosen't works good for my needs.
I've made this tool just to find an oil pan for my car, which was really hard to get because the market has a lot of these, but not for my engine generation.

## How to install SUMP?
```
git clone https://github.com/mtydev/sump
```
Then open cmd in sump directory and enter:
```
pip install -r requirements.txt
```

## How to use SUMP?
```
python ./main.py -u "URL" -k keywords -o output.txt
```
Disclaimer: Please provide url after searchin for an item. For example if you are searching for a car just enter the search phrase in the search box, and then copy link and paste it to -u. Also, You need to enter keywords after space insted of using ",". Don't know why it's like this but I'll leave it for now.

## What do I plan to implement next?
- Maybe make it as jupyter notebook for better data analytics? Then make some options for finding cheapest item in particular keywords?
- Maybe add discord bot support for it?
- Make option for writing result to output file as not needed to run script.
