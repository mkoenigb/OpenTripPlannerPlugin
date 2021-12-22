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

# License
OpenTripPlanner Plug-In for QGIS: © by Mario Königbauer 2019 - Today under GNU General Public License v3.0
