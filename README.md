# Saturday Data science

## TL;DR

- Monthly police auction results.
- So far 2+ years of auction 5000+ results with 3000+ cars.
- Aside from make and model, engine specification, and color, more is available, amounting to 100+ features.
- Features can be used to predict pricing.
- Images can be used for classification.

## Change log
- February 2024:
    - Do prediction of price with separate notebooks. Use "shelve" to store models between notebooks.
    - Add tree model to predict price.
- November 2022: 
    - Added NHTSA data ([see their website](https://vpic.nhtsa.dot.gov/api/)).
- September 2022: 
    - Upgrade to Python 3.10 and upgrade of several packages ([See: `../assets/python-env-20220914.txt`](./assets/python-env-20220914.txt)). 
    - Added new model and extended with engineered features.
- June 2022: Textual changes
- January 2022: Also retrieve inspection info (APK) from RDW
- June 2021: 
    - Cleaner notebooks by deleting outputs before committing
    - Auctions are bi-monthly
- January 2021: Major changes
    - General overhaul
    - Auction lot parsing now done within a Class
    - Configuration settings in .cfg file
    - Outsourced reading re patterns.
    - Linked commenting in notebooks
    - Included fields nr of owners and "WOK" from webportal.
    - ... and more
- October 2020: 
    - Auctions were cancelled due to pandemic. IRS auctions are suspended as yet.
    - Some functions are outsourced.
- January 2020 (Major): 
    - Used mplstyle for figures. 
    - Added gearbox type to classifier. 
    - Enabled IRS auction downloads. Results were added to the website in May 2019.
    - Tested masking with R-CNN
- October 2019: Reorganized landing page
- September 2019: split results section, catch NAP exception when presented before odometer reading.
- August 2019: Added model with Lasso regularization, introduced classification
- July 2019: Add categorical MLR model
- June 2019: Add features based on conformity codes
- May 2019: _Belastingdienst_ (IRS) now also lists auctions on DRZ website. URL has changed.
- April 2019: Query with Socrata Query Language (SoQL)
- March 2019: Add MLR models
- February 2019: Combine features as usage intensity. Another change on the results website: The URL now contains the name of the month.
- 2014: First download of results

Future plans

- save models as .pkl
- Use R-CNN to mask images for classification
- Analyse power (model performance as function of data set size)
- Save data as (relational) database


## Take me to the results right away!

Alright. [Here you go: `./results/`](./results/)

## Sequence of analysis steps

The analysis pipeline is a sequence of Jupyter notebooks that are run in sequence. The notebooks can be found under [`./code/`](./code/) and can be divided in roughly three phases: 1. Scrape, 2. combine and preprocess, and 3. modelling.

## Can I get the data?

I have not included data in this repo. Hence [`./data/`](./data) remains mostly empty (I've added .pkl and .jpg files to my [`.gitignore`](./.gitignore)), but all analyses point to that directory. You can start scraping yourself and fill that directory. If you need historical data you can reach out to [me](https://r5atom.github.io/).

## Little bit of background

Here you can follow what I am doing on a Saturday (and sometimes [other days](https://github.com/r5atom/Saturday-Datascience/graphs/commit-activity) too). 

A project I am working on involves **Police auctions** held twice a month by the Dutch authorities: [Dienst Domeinen Roerende Zaken](https://www.domeinenrz.nl/) (or _DRZ_). The results of the auction [^1] are published. 
Initially I set out to get a bidding advantage in a future auction by using prior auction results. In a way I was setting myself up for a prediction modeling project!

What makes this project interesting is that I did the full pipeline from data engineering to analysis: Scraping data > Cleaning up > Combining data sets > Modeling. 

Although the published auction results are relatively clean, there is enough "dirt" to make it challenging for data cleaning.

![drz-home](./assets/drz-home-square.png)  
_Screenshot of website_

I started working on this in 2014, but I've been systematically been collecting results for many years now. All sorts of lots (goods) are auctioned off: Cars, trucks, motorcycles and trailers, but I've been focussing on getting the results on cars cleaned.

To interpret the auction results, I realize it helps to know a little Dutch. For instance the date format is "day first": dd-mm-yyyy and the decimal separator is `,` and the thousand separator is `.`. One thousand euros and forty two cents is formatted as `EUR 1.000,42`.  
I've tried to translate the results into meaningful field names. Here below I've added a glossary, but if something remains unclear you can always raise an issue.

### Who am I?

You can get that information on [this page](https://r5atom.github.io/).

- - - -

# Glossary

| Term                  | Description |
| --------------------: | :---------- |
| Lot                   | Article for sale |
| LPG                   | Autogas, _liquefied petroleum gas_ |
| [_Dutch_]             | _Translation_|
|           Kavel       | Lot |
|           Brandstof   | Fuel |
|           Versnellingsbak | Gearbox |
|           Merk        | Brand |
|           Vermogen    | Engine power (HP) |
|           Vrachtwagen | Truck (heavy)|
|           Bestelwagen | Delivery truck |
|           APK         | Vehicle inspection, MOT test. "_Algemene Periodieke Keuring_" |
|           DRZ         | Agency that holds police auctions. "_Dienst Roerende Zaken_" |
|           Rdw         | Department of Transportation, DOT. "_Dienst Wegverkeer_" |
|           Belastingdienst | National tax service |
|           BPM         | Registration Tax. "_Belasting van personenauto's en motorrijwielen_" |
|           NAP         | Certification of lawful odometer. "_Nationale Auto of Pas_" |
|           WOK         | Under survey. Needs assessment by Rdw. "_Wachten op keuren_" |
|           OVI         | Online vehicle information. "_Online Voertuig Informatie_" |

**Engine displacement** (or cylinder volume) is expressed _cubic centimeters_, typically abbreviated as _cc_, and the SI standard unit is cm^3. Conversion from cc units to cubic inches (CID, in^3) is `y = x / 2.54^3`, where `x` is volume in cm^3 and `y` the conversion to in^3.

- - - - -
## Footnotes
[^1] _Auction vs. tender_  
Formally the way lots are handled in these kind of auction are by invitation to bid through a "tender". The difference is that bids in an auction are public, and in a tender they are not. It is a sort of silent auction.  
For simplicity I will use the term _auction_.

