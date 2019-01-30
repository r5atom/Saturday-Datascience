# Saturday Datascience

Here you can follow what I am doing on a Saturday (and sometimes other days too).  

A project I am working on involves **Police auctions** held once a month by the Dutch authorities: [Dienst Domeinen Roerende Zaken](https://www.domeinenrz.nl/) (or _DRZ_). The results of the auction [^1] are published. 
Initially I set out to get a bidding advantage in a future auction by using prior auction results. In a way I was setting myself up for a prediction modelling project.  

What makes this project interesting is that I did the full pipeline: Scraping data > Cleaning up > Combining data sets > Modelling.  
The presented auction results are relatively clean, but with enough "dirt" to make it exciting.


![drz-home](./assets/drz-home-square.png)  
_Screenshot of website_

To interpret the auction results, I realize it helps to know a little Dutch. But, I've done most of the work translating the results into meaningful field names. If something is unclear, online translators are your friend or contact me.

## Step 1: scraping the results

Initially results were published on a downloadable .pdf file. 
In the past I've selected the text manually and copied it to a text file, which I parsed with workable, but not so pretty _Matlab/Octave_ code.
Those old routines have since been archived.  

The way the results are published have changed too. They are now available on a website, which I decided to scrape with homebrew _python_ routines that use _pandas_ and run from a _jupyter notebook_. Initially   

The website is subject to change once in a while, and sometimes it feels I am aiming at a moving target, but this keeps it challenging. 

## Step 2: adding extra information

Most lots are vehicles with a registration. An API query gives additional information about the registration. The Dutch equivalent to the DMV does a pretty good job maintaining an open data dataset. It is well documented and updates are communicated. The agency is know as [Dienst Wegverkeer](https://www.rdw.nl/information-in-english) (or _RDW_).


## Step 3: EDA

...

## Step 4: aggregate into one dataset

...

## Step 5: some more EDA

...


## Step 6: modelling

...

# Future

Because the lots have pictures too, a future plan is to do some image classification on these pictures.



- - - - -
[^1] _Auction vs. tender_  
Formally the way lots are handled in these kind of auction are by invitation to bid through a "tender". The difference is that bids in an auction are public, and in a tender they are not. It is a sort of silent auction.  
For simplicity I will use the term _auction_.