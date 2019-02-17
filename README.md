# Saturday Data science

## TL;DR

- Monthly police auction results.
- So far 2+ years of auction 5000+ results with 3000+ cars.
- Aside from make and model, engine specification, color, and more is available, amounting to 100+ features.
- Item features can be used to predict pricing.
- Images can be used for classification.

- - - -

Here you can follow what I am doing on a Saturday (and sometimes [other days](.,/../graphs/commit-activity) too).  

A project I am working on involves **Police auctions** held once a month by the Dutch authorities: [Dienst Domeinen Roerende Zaken](https://www.domeinenrz.nl/) (or _DRZ_). The results of the auction [^1] are published. 
Initially I set out to get a bidding advantage in a future auction by using prior auction results. In a way I was setting myself up for a prediction modeling project!  

What makes this project interesting is that I did the full pipeline from data engineering to analysis: Scraping data > Cleaning up > Combining data sets > Modeling.  

Although the published auction results are relatively clean, there is enough "dirt" to make it challenging for data cleaning. 


![drz-home](./assets/drz-home-square.png)  
_Screenshot of website_

I started working on this in 2014, but I've been systematically been collecting results for about two years now. All sorts of lots (goods) are auctioned off: Cars, trucks, motorcycles and trailers. I've been focussing on getting the results on cars cleaned.

To interpret the auction results, I realize it helps to know a little Dutch. For instance the date format is "day first": dd-mm-yyyy and the decimal separator is `,` and the thousand separator is `.`. One thousand euros and forty two cents is formatted as `EUR 1.000,42`.  
I've tried to translate the results into meaningful field names. Here below I've added a glossary, but if something remains unclear you can always raise an issue.

## Step 1: Scraping the results [(notebook)](./code/scrape-drz-auction-results.ipynb)

Initially results were published on a downloadable [.pdf file](./assets/201410-catalogusdrz.pdf). 
In the past I've selected the text manually and copied it to a text file, which I parsed with workable, but not so pretty _Matlab/Octave_ code.
Those old routines have since been archived.  

The way the results are published have changed since and they became available on a website. I've decided to scrape these results with home-brew _python_ routines that use _pandas_ and run from _Jupyter notebooks_. Initially I used clunky solutions like `str.index` to find patterns in the text, but recently I started using [regular expressions](https://en.wikipedia.org/wiki/Regular_expression) (regex). This is more powerful and maintains a clean workflow. The regex patterns are stored in .csv files: [./code/regexp-patterns](./code/regexp-patterns).

![drz-result](./assets/drz-result-190022405.png)  
_Screenshot of an auction result. This example lot was sold in February 2019 for EUR 35,290.00 (about $40.000)_

![regex-example](./assets/regex-selection-190022405.png)  
_Example of how a *regex* pattern is used in parsing text. In this case the odometer value follows the text `Km-stand`, which might also be in lower case._

The drz website is subject to change once in a while [^2], and sometimes it feels I am aiming at a moving target, but this keeps it challenging. 



### Known issues
- Occasionally lots are a combination of multiple items. Currently only the first item will be handled, however I also store the raw text for future provisioning.

## Step 2: adding extra information [(notebook)](./code/add-rdw-info-to-drz.ipynb)


Most lots are vehicles with a registration. The Dutch equivalent to the DMV know as [Dienst Wegverkeer](https://www.rdw.nl/information-in-english) (or _RDW_) provides an API service where registration can be queried. This gives additional information about vehicles that is not in the auction results such as engine capacity.

![rdw-result](./assets/rdw-engine-85zpl9.png)

The RDW does a pretty good job maintaining this open data dataset. Definitions are [well documented](https://opendata.rdw.nl/Voertuigen/Open-Data-RDW-Gekentekende_voertuigen/m9d7-ebf2). They have a [google forum](https://groups.google.com/forum/#!topic/voertuigen-open-data/rnwGKL-HQ8Y) where updates are communicated.

## Step 3: EDA [(notebook)](./code/explore-auction-results.ipynb)

With the scraped and results I can do some basic **E**xploratory **D**ata **A**nalysis.


## Step 4: aggregate into one dataset [(notebook)](./code/aggregate-all-auctions.ipynb)

In this step all auction results are merged into one dataset. All cars are selected and saved to disk in `.pkl` format.

## Step 5: some more EDA

...


## Step 6: modeling

...

# Future

## Image classification

The auction results have pictures too, a future plan is to do some image classification on these pictures. I've added a notebook that downloads images for future use.

### Download images [(notebook)](./code/download-images.ipynb)

Lots contain information such as brand and model, color, registration number. This can be used for supervised learning. The background in the images are pretty standardized and could make things easier.




# Glossary

| Term            | Description |
| --------------: | :---------- |
| Lot             | Article for sale |
| [_Dutch_] Kavel | Lot |
| [_Dutch_] APK   | Vehicle inspection, MOT test. "_Algemene Periodieke Keuring_" |
| [_Dutch_] DRZ   | Agency that holds police auctions. "_Dienst Roerende Zaken_" |
| [_Dutch_] Rdw   | Department of Transportation, DOT. "_Dienst Wegverkeer_" |
| [_Dutch_] BPM   | Registration Tax. "_Belasting van personenauto's en motorrijwielen_" |

- - - - -
[^1] _Auction vs. tender_  
Formally the way lots are handled in these kind of auction are by invitation to bid through a "tender". The difference is that bids in an auction are public, and in a tender they are not. It is a sort of silent auction.  
For simplicity I will use the term _auction_.

[^2] _Feb 2019_: Another change on the results website: The URL now contains the name of the month.
