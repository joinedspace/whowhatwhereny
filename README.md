# whowhatwhereny
A visual exploration of correlations between various census demographics and land-use at the neighborhood level in Manhattan, New York.

## Who is this for?

This is for everybody. Making open data visually enticing and (relatively) uncluttered is always the end goal. Mapping human data does more than satisfy a curiosity. It's a way of legitimizing an aggregated condition. While needing to trade nuance for sweeping hypotheses can be off-putting, the ability to show statistical relationships is hugely valuable as a corroboration of the anecdotal.


## How do I use the dashboard?

Selecting a pair of variables at the top left of the dashboard updates the map of Manhattan. The color distribution represents the Pearson's correlation score between the selected variables at the neighborhood level. Hatched areas indicate a negative correlation.

This correlation pair is the very same as that shown in the scatter plot underneath the map.

The top right map of the dashboard displays the selected Manhattan neighborhood with a choropleth of the selected display variable. This also updates the geographical location represented by the scatter plot.

Play around with the three dropdowns and see how the visualizations change.


## Why those particular variables?

Land-use as a proxy for the state of the built environment was the cornerstone dataset, with key variables of mixed-use and residential-use distributions among other zoning types.

ACS variables of median age, median income, and % racial minority were chosen as the primary demographic metrics, as a dive into socioeconomic correlations to neighborhood makeup seemed pertinent.


## What exactly does all of this show?

Unsurprisingly, many of the correlative relationships were inconclusive. The totality of phenomena is too large to list out here, but an example of an interesting emergence is as follows.

Considering the variable pair "% residential zoned" and "% racial minority", three neighborhoods have significantly negative results: the West Village, West Harlem, and Turtle Bay. The first two have the stronger correlations (roughly -0.5 each). What is interesting is that both of these neighborhoods are college districts, housing NYU and Columbia respectively. Is it a stretch to posit that census individuals housed in university property are likely less diverse than populations outside?

It certainly warrants another look.

A more general takeawy has to do with mixed-use zoning. The results here would suggest that there is very little widespread correlation between a neighborhood being more mixed-use and suffering from socioeconomic chasms as a result of say, gentrification. In order to make more firm statements, a time-series of zoning would allow for more interesting regression analysis, but this certainly seems to be a check in the box favoring mixed-use zoning.


## Where is the data from?
TODO


## Are there caveats in the results?
TODO
