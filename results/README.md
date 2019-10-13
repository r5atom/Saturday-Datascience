# The peril of round bids

In auctions where the bid price is not made public the winning bid could have been outbid by only small difference. A common strategy is to **avoid round bids** (e.g. _EUR 100_). For instance an intended bid of _EUR 4200_ can be submitted as _EUR 4201_. With the extra euro you buy yourself the edge of outbidding the other bidder! However other bidders could do the same.  
In attempt to see where the balance is between outbidding and adding a little to your intended bid, I've investigated the last two digits of the prices in the auctions. Because only the winning bid is made public, the distribution of all the bids is unknown and strategic bidding prices remain invisible. But still this analysis might give an indication of where to strategically put a bid.

![F1](./last-two-digits.png)  
_Figure 1. Last two digits of all winning bids. The last digits (0, 1, .. 8, 9) are on the abscissa. The decimal digits (10, 20, .. 80, 90) are on the ordinate. The lower left square contain bids ending with `00` (E.g. `1100`, `100` or `4200`). The upper right are bids ending with `99` (`4299`, `99`, ..). The number of bids are shown as color intensity. If the occurrence is homogenous for all numbers, the occurrence would be the total number of bids divided by the possibilities ($10 \times 10 = 100$). On April 2019 this was around $3000/100 = 30$ times (Note: data have been added since and n > 3000). This is the (expected) average of occurrence and indicated in **white**. **Blue** indicates above average occurrence (saturating at 10 times the expected value) and **red** is below average (saturating at 1/10 of the expected value). The number of occurrences of the five most and least occurring digit pairs are labeled inside the colored squares (e.g. `00`)._

Fig. 1 shows bids ending with `00` are most frequent and occurs 10x more than expected. A higher bid ending with `01` could have outbid these items. Other frequent occurring bids (blue) end with `11`, `50`, `55` and `77`. Figure 1 appear to show a blue-to-white diagonal ($x = y$). This indicates that bids with the same digits (`11`, `22`, `33`, ..) appear to be frequent. Bids with `4` as the last digit are not so frequent. This can be seen by a red vertical band at $x = 4$. Bids ending with `92` and `94` occur only a few times (dark red). It might be a good strategical advantage to use a bid ending with these values (however note the caveat not knowing all bids to this conclusion here above). Increasing a bid with close to EUR 100 might not be worth the edge, however a less expensive cost is to choose to end a bid with `32`, which has only occurred a few times since 2017.

# Combining features: Usage intensity. wear and tear

The intensity of usage determines the value of a car. Usage can be expressed as age and/or as distance travelled.

![F2](./odometer-ecdf.png)  
_Figure 2. Distribution of odometer reading expressed as cumulative density function (empirical cdf, ecdf). An ecdf is constructed by sorting values from small to large and at every value the graph is increased with `1/n`, with `n` being the number of data points. The resulting graph reflects the fraction of data `y` that is smaller than value `x`. Individual data points underlay the gray ecdf. Overlapping data points appear darker and are an extra visual aid indicating steepness of the ecdf. Note that distance is expressed as units of 1000 km ($10^6$ m, Mm)._

Fig. 2 show the distribution of all odometer readings. These readings vary from 0 to >800,000 km. The median ($y = 0.5$) is around 180,000 km. The distribution appears to be approximately linear, thus uniformly distributed. This is also visible as the uniform gray shade in the data points.

![F3](./age-ecdf.png)  
_Figure 3. Distribution of age of cars (ecdf, see caption fig 2. for explanation). Top panel show the full distribution. The lower panels show the same data, but separated in two panels at 20 years (left: young cars, <20 year, right: old cars, >20 year). Note the different scale of the lower-right panel._

The distribution of car age is shown in figure 3. The top panel shows a long tail of cars at age >20 year. These are also shown in the lower-right panel. The lower-left panel zooms in on cars younger than 20 year. The distribution appears uniform (linearly increasing ecdf), but with some increased density at 5 and 15 year old cars.

Cars of comparable age can have different level of usage. To account for age the odometer can be expressed as function of age. 

![F4](./usage-dist.png)  
_Figure 4. Distribution of usage per unit of time. Note that x-axis is in log-units. Top: ecdf (see caption fig. 2), Bottom: histogram. The median usage per day is indicated in blue._

Figure 4 shows that the usage per unit time appears to be log-normally distributed. Cars with lower than median usage are <45km/day and can go as low as a few km/day on average. High intensity usage can go beyond 100 km/day. Note that a brand new car (1 day old) with a 150 km reading falls in one of the extreme usage bins.

![F5](./usage-regression.png)  
_Figure 5. Regression of age and odometer reading. Every dot is a car with a certain age and odometer reading. The lower left are young cars with low odometer readings. The upper-right are older cars with high odometer readings. The average (see fig. 4) use is indicated as a blue line. Lower and higher intensity usage (20, 40, 80 and 160 km/day), are indicated as dotted lines._

Fig 5. shows that age and odometer reading correlates. This is not unexpected. The slope of the correlation indicates the usage per unit of time. The average use is not a perfect prediction of the usage of all cars. Some old cars (>10,000 days) have an usage intensity below 10km/day. It also appears the data curves upwards. Meaning young cars have relative low intensity usage (>40 km/day) and older cars (~5000 days or ~15 year) have usage intensities well beyond 40 km/day.

Figure 6 shows the same data on a log-log axis. This enables a better view on other than linear correlation and whether the relation is according to a [power law](https://en.wikipedia.org/wiki/Power_law).

![F6](./usage-regression-loglog.png)  
_Figure 6. Usage intensity. Same data as figure 5 on a log-log scaled axis. Here the dotted lines are usage intensity proportional increasing or decreasing with age. The blue line indicates intensity of usage that remains the same across all ages. Dotted lines above this average usage indicate an increase in intensity with age, and below the blue line a decrease of usage intensity._

Although the data seem to follow the average usage well, young cars appear to have lower intensity usages as most data fall below the blue line. It appears the data follows a steeper relation than linear (blue), indicating an exponential increase of usage with car age. A power of 1.5 seem to approximately match the data.  
Intuitively one would asume that usage intensity would go down with car age, thus a exponential decay (shrinkage) associated with a power smaller than one (e.g. $y = x^{0.5}$ in fig. 6). In general this is not the case, but there is a clear subset of old cars (~10,000 days or ~30 years) where usage intensity is below average and drops exponentially.  

Another observation can be made in both figures 5 and 6. A subset of high intensity usage of cars are visible slightly below 200,000 km and ages ~1000-2000 days (~3-5 years). The intensity of usage is markedly higher than average with ~100 km/day. This is possibly the result of a business policy. Lease or rental companies might choose to renew their fleet when cars have odometers around 200,000 km. The car purpose (company cars) might explain the high intensity usage.

In conclusion, the average usage (~45 km/day) might not be the best way to assess other than usual usage (and consequently value). It might be better to model usage with a higher order function.  
Another likely confound to the above analysis that diesel cars on average are used more intensely. This is part due to Dutch tax rules: compared to gas the fuel price is lower, but the fixed road tax is higher. The relation of value and usage intensity might be different for different types of fuels.  
Furthermore it might be best to treat subsets of cars differently. Older cars might be used for recreational purpose only, and the usage intensity might have an lesser effect on their value.

- - - - 
# Predicting winning bids

To predict winning bids, the approach is to use information about the lots and use a regression model to describe the bid prices. This approach is described in detail [here](./regression-models.md). Several linear models are presented with increasing complexity.

![F7](./model-performance.png)  
_Figure 7. Coefficient of determination as measure of fit performance of all linear models examined. With every new model the aim is to improve the accuracy of the prediction, thus increasing $R^2$. $R^2$ is determined with cross validations, hence every model has multiple observations for $R^2$. The model with reduced observations appears to have the best performance, however it ignores observations with missing values and the number of observations is reduced._

## The current model: Lasso with categorical data included.

After exploring several models the model with Lasso regularization appears to return a reasonable predictor for bid price that generalizes well. The model uses many features, but the coefficients are constrained to prevent them to become very large. This usually occurs when features are colinear. The regularization term ($\alpha$) was determined with a grid search.

![F8](./MLR_Lasso.png)  
_Figure 8. Result of Multiple Linear Regression (MLR) with categorical and numerical features. The coefficients are constrained with Lasso regularization. Bar height indicate coefficient of the features. Features may correlate positively or negatively indicated by the sign of the coefficient. When the bar height is small a value is shown. Features are sorted in descending order. The dashed lines bound coefficients that are zero. The top panel shows the numerical features. The first bar indicates the offset. The panels below the top panel are the categorical features. As with the numerical features the coefficients are sorted as well. The third panel show that luxury brands like "Rolls-Royce" are left of the vertical dashed line and positive contributors to the auction price._

- - - -
# Classifying images

The dataset also contains images of the auction lots. These can be used for classification and is described in detail  [here](./classification-models.md). Figure 9 shows an example of all available pictures of a single auction lot. In an attempt to identify the car brand the front view (ex. fig. 9a) of the lot is used to train several classification models.

| A) Front | B) Rear | C) Interior |
|:-----:|:-----:|:-----:|
| ![F9a](../assets/2019-9-2209-00.jpg) | ![F9b](../assets/2019-9-2209-01.jpg) | ![F9c](../assets/2019-9-2209-02.jpg) |

_Figure 9. Three views of example lot 2019-9-2209._

The model performance can be expressed in F1 score and the tested models yield different results.

![F10](./model-performance-classification.png)  
_Figure 10. F1 scores as measure of classification performance for all models._
