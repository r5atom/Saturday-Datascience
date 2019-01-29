# Saturday Datascience

Here you can follow what I am doing on a Saturday (and somtimes other days too).  

A project I am working on involves **police auctions** held once a month by the Dutch authorities. The results of the auction [1] are published. 
Initially I set out to get an advantage in a future auction by using prior auction results. In a way I was setting myself up for a prediction modelling project. 

## Step 1: scraping the results

Initially results where published on a downloadable .pdf file. 
In the past I've selected the text manually and copied it to a text file, which I parsed with workable, but not so pretty _Matlab/Octave_ code.
Those old routines have been archived since.  

The way the results are published have changed too. They are now available on a website, which I decided to scrape with homebrew _python_ routines that use _pandas_ and run from a _jupyter notebook_.  

## Step 2: adding extra information

_TODO: RDW_

## Step 3: EDA

...

## Step 4: aggregate into one dataset

...

## Step 5: Some more EDA

...


## Step 6: modelling

...

# Future

Because the lots have pictures too, a future plan is to do some image classification on these pictures.




[1] Auction / tender  
Formally the way lots are handled in these kind of auction are by invitation to bid through a "tender". The difference is that bids in an auction are public, and in a tender they are not. It is a sort of silent auction.  
For simplicity I will use the term _auction_.