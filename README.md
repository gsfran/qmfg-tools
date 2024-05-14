# Rapids Production Dashboard


## Overview

Rapids Production Dashboard is a web application created to facilitate daily operations in my current role as an engineer in medical device manufacturing. It seeks to provide helpful and easy-to-use tools for managing production and coordinating business needs across functional groups. This is not intended to be used externally, however it has been built to be extensible and could support many different applications.

## Live Demo
* [PythonAnywhere](https://gsfran.pythonanywhere.com/)

## Features

* Clean, simple GUI dashboard allows users to:
    * Create and schedule work orders through dependent processes
    * Track and forecast order progress automatically
    * Coordinate cross-functional resources
    * Customize the default production schedule
    * Adjust for holidays/one-off schedule changes
    * Access centralized visual management tools
* Integrated ORM compatible with any RDBMS
* Automated and purpose-built ETL microprocess
* Configurable Overall Equipment Effectiveness (OEE) analysis metrics

Planned feature updates:
* E-mail alerts to stakeholders/other parties of interest
* Option to forecast using a standard rate vs. an extrapolated rate
* Operator utilization input via webform to replace use of MS Excel
* HTTP, WSGI, MySQL server set-up and implementation
* Automated real-time monitoring and predictive maintenance service
* Implement automated testing and further adoption of TDD principles
* Additional sensor types for each production line w/ comparative analysis


## Conception

Originally started to pull production data from spreadsheets, my first python scripts were what you'd expect -- basic but functional. My job was to report this data, and identify ways to improve productivity. The data was user-input and prone to misentries, so automated analysis and reporting was a difficult thing to implement reliably. Still, I was curious if any trends could be identified after some manual data cleaning and indeed it was interesting. 

Soon after, the dimensions of some purchased material became of great concern. A sensor hooked up to LabView was already measuring and recording this data, outputting it to a shared network drive. The data was noisy, and nigh impossible to correlate with the actual machine output in any meaningful sense, but there was some useful information to gain from it. I learned to use *bokeh* to visualize the data on scatterplots and histograms, attempting to correlate it with the issues facing production with varying degrees of success. 

Some time later I learned the vision systems in use could write to file via FTP. Finally, I had an objective data source which directly correlated to production output. I spent some time generating nice charts and graphs with a script 1k+ lines long, but eventually realized the trap I'd fallen into. Everything was hard-coded, very little was commented, and nobody else could really use this program without installing a bunch of python libraries on their work computer. Turning what I had into an interactive dashboard was going to take some work. So the project was refactored, first with an OOP approach but still within a single file (spaghetti.py), then eventually into a fully-fledged library intended to be imported into a future user-facing application.

Around this time, a major opportunity for my organization was in scheduling work orders, receiving and communicating progress updates, and coordinating critical actions across different departments. I had the idea to recreate the years-old Excel-based schedule that was causing so much headache into a live dashboard that anyone could access. Researching deployment methods, I realized a standalone package or program was not going to be practical, and also that a centralized data source required a centralized data server. A web app satisfied all of these requirements, could very easily manage and interact with a centralized database, and could be accessed by anyone with access to the internal intranet.


## Key Technologies

This project is written almost entirely in python. Notable libraries include:
* *Flask* -- web app framework with useful extensions:
    * *Flask-SQLAlchemy* -- ORM support via SQLAlchemy
    * *Flask-WTF* -- form validation and security via WTForms
    * *Flask-Migrate* -- CLI tools for database migration via Alembic
    * *Flask-Login* --  user access control and session handling
* *Jinja2* -- endpoint templating/dynamic styling
* *pandas* -- Data analysis/manipulation
    * Production performance and reporting
    * Scheduling logic done entirely within datetime-indexed dataframes
* *python-dotenv* -- environment variable handling
* *venv* -- virtual environment handling
* *bokeh*, *matplotlib* -- data visualization

SQLite provided a simple and easy SQL deployment during development, for production deployment a dedicated MySQL server would be best.

This repository also includes custom python ETL tools for acquiring data:
* Plaintext csv generated by equipment sensors
* Operator reports saved in Excel format (.xlsx)

Considerable time was spent re-familiarizing myself with HTML/CSS and creating a UI/UX that was functional and pleasing. While not the main focus of this project, I still wanted the front-end to express my initial vision accurately -- and eventually it did!


## Dependencies and Deployment

* HTTP Server production-grade web server (Apache, Nginx)

* WSGI Server -- interface between the web server and the python backend (mod_wsgi, Gunicorn)

* MySQL Server -- much better performance and scalability than the SQLite currently implemented

* SSO Integration -- inbuilt login functionality is minimal and not intended for production use



run `pip install -r requirements.txt` to install python dependencies

`.env` file -- see `.env.example` for required keys and value datatypes


## Lessons Learned

There's always more abstraction to consider. The importance of designing systems ahead of building them is shown by the numerous refactorizations this project has undergone.

If I were to do this over, I would start with a frontend framework such as React.js and develop that from the ground up. The additional capabilities provided by Javascript would allow greater use of the modern visual style I've strived to implement:
* Dragging and dropping a work order to load, park, etc.
* Tabbed pages for process groups
* Scalable dashboard views, e.g. 1-hour to 1-year


## Helpful Links

* [Miguel Grinberg's *The Flask Mega-Tutorial.*](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world)

## License
Copyright (C) 2023 Garrett Francis

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program.  If not, see <https://www.gnu.org/licenses/>.
