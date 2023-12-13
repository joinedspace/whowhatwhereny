# whowhatwhereny
A visual exploration of correlations between various census demographics and land-use at the neighborhood level in Manhattan, New York.

## Who is this for?

This is for everybody. Making open data visually enticing and (relatively) uncluttered is always the end goal. Mapping human data does more than satisfy a curiosity. It's a way of legitimizing an aggregated condition. While needing to trade nuance for sweeping hypotheses can be off-putting, the ability to show statistical relationships is hugely valuable as a corroboration of the anecdotal.
	
To put it simply, this is a proof-of-concept for the larger end goal of democratizing not just data access, but visualization, analysis, and theory-making.


## How do I use the dashboard?		

1. Select a pair of variables at the top left of the dashboard to update the map of Manhattan.
	
2. The color distribution represents the Pearson's correlation score between the selected variables at the neighborhood (community district) level. Hatched areas indicate a negative correlation.
	
3. This correlation pair is the very same as that shown in the scatter plot underneath the map.
	
4. The top right map of the dashboard displays the selected Manhattan neighborhood with a choropleth of the selected display variable. 
	
5. This also updates the geographical location represented by the scatter plot.
	
6. Play around with the furthest right dropdown to change the selected display variable from step 4.

## What exactly does all of this show?

Unsurprisingly, many of the correlative relationships were inconclusive. The totality of phenomena is too large to list out here, but an example of an interesting emergence is as follows, and the poster file in this submission packet goes into more depth on this topic.
	
Considering the variable pair ``\% residential zoned" and ``\% racial minority", three neighborhoods have significantly negative results: the West Village, West Harlem, and Turtle Bay. The first two have the stronger correlations (roughly -0.5 each). What is interesting is that both of these neighborhoods are university districts, housing NYU and Columbia respectively. Is it a stretch to posit that the extensive purchasing of residential property by these universities results in displacement, gentrification, and lower diversity than populations outside?
	
A lot of literature supports this statement, and it's a general topic that certainly warrants significant investigation.
	
A more general takeaway has to do with mixed-use zoning. The results here would suggest that there is very little widespread correlation between a neighborhood being more mixed-use and suffering from socioeconomic chasms as a result of say, gentrification.A time-series of zoning would allow for a more robust analysis, but this certainly seems to be a check in the box favoring mixed-use zoning.
	
In the end, the purpose of this project was to democratize data visualization, so play around with combinations of variables and see what sorts of trends emerge!

## Where is the data from?
<p>    
                <a href = "https://data.census.gov/"> US Census Bureau Demographic Data</a>, 
                <a href = "https://data.cityofnewyork.us/City-Government/Community-Districts/yfnk-k7r4"> DCP Community Districts</a>,
                <a href = "https://data.cityofnewyork.us/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO-/64uk-42ks"> 
                DCP MAPPLUTO</a>,
                <a href = "https://data.cityofnewyork.us/City-Government/2020-Census-Tracts-Mapped/weqx-t5xr"> 
                ACS Census Tracts</a>,
                <a href = "https://data.cityofnewyork.us/City-Government/Zoning-Application-Portal-ZAP-Project-Data/hgx4-8ukb"> 
                DCP Zoning Application Portal</a>.
                </p>


## Are there caveats in the results?
  The p-value threshold was chosen as 0.1, which is more lenient than the commonly seen 0.05. 
               In truth, the p-value threshold is arbitrary and relative, not absolute, values should be the focus here. 
               Gaps in regions of the choropleth maps are the result of missing or corrupted data. 
               Gaps in regions of the Manhattan map mean that the neighborhood did not have a statistically significant correlation. 
               Several correlation pairs were insignificant city-wide (3 of 10). These were omitted from the dropdown. 
               The site performance can and will be optimized as some of the graphics load slowly (large file sizes). 
               Zoning in New York is sometimes outdated in its labeling and not necessarily abided by. For instance, 
               Tribeca supposedly contains no residential zoning, but people do live there. A look at the ZOLA portal confirms this phenomenon. 
               This adds another layer of complexity to the analyses, because it puts into question the validity of the zoning data. 
