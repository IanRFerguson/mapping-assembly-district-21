# mapping-assembly-district-21

<img src="./static/images/rbs.png" width=65%>

This is a full-stack web application developed to track voter outreach in Assembly District 21 prior to election day (November 2022).


## Usage Notes

This app is designed to be user friendly! The end user can input either an exact address (`Fine Grain`) or select a precinct broadly (`Coarse Grain`), along with the type of outreach conducted (e.g., phone banking, text banking, canvassing, etc.)

<img src="./static/demo/form.png" width=65%>

<br>

The user's selections are pushed to a `SQLite` database, where **counts per precinct** are aggregated and mapped.

<img src="./static/demo/map.png" width=65%>