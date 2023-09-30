# qmfg

## Overview

QMFG is a web application created to facilitate daily operations in my current role as an engineer in medical device manufacturing. It seeks to provide helpful and easy-to-use tools for managing production and coordinating business needs across functional groups. This is not intended to be used externally, however modules could certainly be developed for any process and integrated with minimal refactorization.

## Features

* Clean, simple GUI dashboard allows users to
    * Create and schedule work orders through dependent processes
    * Track and forecast order progress automatically
    * Customize the production schedule (indefinitely, or for a single week)
    * Access centralized and secure visual management -- operator to CEO
* Integrated ORM compatible with any RDBMS
* Automated and purpose-built ETL process
* Hand-tailored and configurable Overall Equipment Effectiveness (OEE) analysis

Planned feature updates:
* E-mail alerts to stakeholders, approvers, etc.
* Selectable forecasting (standard vs. extrapolated rate)
* Operator utilization input via webform directly to relational database
* MySQL server set-up and implementation
* Automated real-time monitoring/maintenance prediction algorithm
* Automated testing implementation/further adoption of TDD principles
* Additional sensor types for each production line w/ comparative analysis


## Why?

To learn, first and foremost. The requirements for supporting this in any official capacity are well outside my experience as a software developer and my role as an engineer, and many trusted and validated market solutions exist to address the very needs I've attempted to with this project.

I enjoy programming and saw an opportunity to apply it to a real-world need. Though that need is no longer there, I continue to develop this project because it's something I enjoy doing for the sake of learning. It naturally led me on a path to acquire many new skills -- all of which were necessary to achieve the outcome I'd first set out on -- and that has been a huge motivating factor. Never did I anticipate building a fully-fledged web application, but I've ended up really enjoying it!

If you're reading this README it's likely you're a potential employer I've linked to my github, in which case you're a very close 2nd reason.


## Conception

Originally started to pull production data from spreadsheets, my first python scripts were what you'd expect -- basic but functional. My job was to report this data, and identify ways to improve productivity. The data was user-input and prone to misentries, so automated analysis and reporting was a difficult thing to implement reliably. Still, I was curious if any trends could be identified with manual data cleaning, and certainly there was some useful information there anyway.

Some time later, a dimension of purchased raw material became a figure of great concern. There was a sensor hooked up to LabView which had already been measuring and recording this data, outputting it to a shared network folder automatically. It was very noisy, and impossible to correlate with the machine output, but again there was some useful data to extract there. I learned to use *bokeh* to visualize the data, and attempted to correlate it with that of the spreadsheet to varying degrees of success. 

After becoming aware that the many inspection cameras already in use could write to file via FTP, I finally had an objective data source for which to develop tools to analyze and report production performance. I spent some time making beautiful charts and graphs with a script over 1000 lines long, only to realize I'd hardcoded in basically everything. Nobody else could really use this program, and turning it into an interactive dashboard would never work with the way it was structured. So the project was refactored, first with an OOP approach but still within a single file (spaghetti.py), then eventually into a custom library intended to be imported into some to-be-developed generic user application.

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

QMFG also includes custom python ETL tools for acquiring data:
* Plaintext csv generated by equipment sensors
* Operator reports saved in Excel format (.xlsx)

Considerable time was spent re-familiarizing myself with HTML/CSS and creating a UI/UX that was functional and pleasing. While not the main focus of this project, I still wanted the front-end to express my initial vision accurately -- and eventually it did!


## Dependencies

HTTP Server -- production-grade web server (Apache, Nginx)

WSGI Server -- interface between the web server and the python backend (mod_wsgi, Gunicorn)

MySQL Server -- better scalability than the SQLite currently implemented, not required but certainly close

SSO Integration -- inbuilt login functionality is minimal and not intended for production use



run `pip install -r requirements.txt` to install python dependencies

`.env` file -- see `.env.example` for required fields and datatypes


## Lessons Learned

There's always more abstraction to consider. The importance of designing systems ahead of building them is shown by the numerous refactorizations this project has undergone.

If I were to do this over, I would start with a frontend framework such as React.js and develop that from the ground up. The additional capabilities provided by Javascript would allow greater use of the modern visual style I've strived to implement:
* Dragging and dropping a work order to load, park, etc.
* Tabbed pages for process groups
* Scalable dashboard views, e.g. 1-hour to 1-year


## Helpful Links

* [Miguel Grinberg's *The Flask Mega-Tutorial.*](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world)

## License

