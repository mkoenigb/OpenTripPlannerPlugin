# OpenTripPlannerPlugin
OpenTripPlanner Plug-In for QGIS lets you access OTP functionalities from within QGIS.

# How To
1. Install the Plug-In
2. Go to "General Settings" Tab and enter a Server URL including the path to the OTP router, which can be accessed without Proxy or Authentification
3. Choose your Settings and hit run
- You can find more details about each setting by reading tooltips on mousehover or checking OTP-API-Docs.

# Notes
- I invite you to add fixes or features via pull requests. If you encounter bugs or issues, please report them on https://github.com/mkoenigb/OpenTripPlannerPlugin/issues
- This plugin only requests routes or isochrones from an OTP instance. It then processes and saves the results delivered by OTP. So in case you encounter issues with your results, dont forget to check your OTP instance too.
- If an error is encountered it will be documented in QGIS message log as well as in the attribute table of the result layer. To prevent the result from having invalid geometries, a dummy geometry at coordinate 0,0 is added in such cases.
- One feature per isochrone time or per route leg is added to the result. So you are free to do whatever you want. You can merge or dissolve the results based on the given IDs if you prefer one feature per route or isochrone.

# Details about OTP API
Note that OTP 2.0 does currently (Dec 2021) not support isochrones. To use Isochrones API use OTP 1.5 or (if already released) a newer version of OTP.
- Details about Isochrone API can be found at http://dev.opentripplanner.org/apidoc/1.0.0/resource_LIsochrone.html
- Details about Plan API can be found at http://dev.opentripplanner.org/apidoc/1.0.0/resource_PlannerResource.html

# Examples
Digitransit (https://digitransit.fi/en/), for example, has a publicly accessible OTP-Server. You can find details how to access it on their website. You can find a list of more OTP-Deployments at https://docs.opentripplanner.org/en/latest/Deployments/.
You can also easily setup your own local OTP instance by following this short tutorial: http://docs.opentripplanner.org/en/latest/Basic-Tutorial/

![example](https://github.com/mkoenigb/OpenTripPlannerPlugin/blob/master/example.jpg)

# What does the "Aggregated Isochrones" function do and how can I interpret the results?
Please note that this function is highly experimental. Expect a Python error when you run it or a crash in the worst case!


If you choose "Raw", no aggregation is done at all and the Plugin does return the raw results for each requested datetime for each feature. 
This can be a mess, but you are free to do whatever you want. It is also useful to debug the results from "Maximum only (via Dissolve)" and "All possible Aggregations (via Union)".


If you choose "Maximum only (via Dissolve)":

1. For each feature a temporary layer is created
2. For each datetime iteration of a feature the isochrones will be stored in that temporary layer
3. If all datetime iterations are done, the temporary layer gets dissolved by time field
4. The dissolved layer's features are added to the output layer

You can interpret this as the most optimistic service area, reachable somewhen during the given timerange. Basically keeping the most optimistic result of each time step.


If you choose "All possible Aggregations (via Union)":

1. For each feature a temporary layer is created
2. For each datetime iteration the response isochrones are processed with the following algorithms: 
   a) Fix geometries
   b) Union 
   c) Join attributes by location (summary): Keeping the minimum time attribute of the overlapping union-parts
   d) Delete duplicate geometries
3. The result of this processing is added to a temporary layer for each datetime iteration
4. If all datetime iterations are done for a feature, the temporary layer is processed the following:
   a) Multipart to Singleparts
   b) v.clean (needed, otherwise Union will most likely fail)
   c) Fix geometries
   d) Union
   e) Delete duplicate geometries
   f) Join attributes by location (summary): Adding all statistical summarys of the Union-result to the Delete-Duplicates-result
   g) Delete all fields except the statistical summarys
5. Add the processed temporary layer's features to the outputlayer

You can interpret the results the following:

- count: the area is reachable x times during the given time range, note how many requests you have done for that range to give this value a meaning
- unique: if greater 1 there are differences in the time needed to reach the area during the given time range
- min: most optimistic service area
- max: most pessimistic service area
- range: if greater 0 or not NULL there are differences in the time needed to reach the area at different times during the given time range by telling how big the greatest difference is (most optimistic to most pessimistic)
- sum: doesnt say anything meaningful at all, better delete it unless you have a great idea what you could do with it
- mean: average reachability of the area within the given time range
- median: median reachability of the area within the given time range

# License
OpenTripPlanner Plug-In for QGIS: © by Mario Königbauer 2019 - Today under GNU General Public License v3.0
