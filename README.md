# qmfg

## Overview

QMFG is a web application created to facilitate operations in my role as an engineer in medical device manufacturing. It seeks to provide helpful and easy-to-use tools for managing production and coordinating business needs across functional groups. This is not intended to be used externally, however modularity has been inbuilt and classes could certainly be developed for any process and integrated with minimal refactorization.

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

I enjoy programming and saw an opportunity to apply it to a real-world need. Though that need is no longer there, I continue to develop this project because it's something I enjoy doing for the sake of learning. It naturally led me on a path to learn many different skills, all of which were necessary to achieve the outcome I'd first set out on, and that has been a huge motivating factor. Never did I anticipate building a web application, but I really enjoyed that part of it too!

If you're reading this README it's likely you're a potential employer I've linked to my github, in which case you're a very close 2nd reason.


## Conception

Originally started to pull production data from spreadsheets, my first python scripts were what you'd expect -- basic but functional. My job was to report this data, and identify ways to improve productivity. The data was user-input and prone to misentries, so automated analysis and reporting was a difficult thing to implement reliably. Still, I was curious if any trends could be identified with manual data cleaning, and certainly there was some useful information there anyway.

Some time later, the height of plastic injection-molded parts on a conveyor became a figure of great concern. There was a sensor hooked up to LabView which had already been measuring and recording this data, outputting it to a shared network folder automatically. It was very noisy, and impossible to correlate with the machine's actual speed, but again there was some useful data to extract from that sensor's output. I learned to use *bokeh* to visualize it, and attempted to correlate the data with that of the spreadsheet to varying degrees of success. 

After becoming aware that the machine's many inspection cameras could output data via FTP, I finally had an objective source of data with which I could develop tools to analyze and report production performance. I spent some time making beautiful charts and graphs with a script over 1000 lines long, only to realize I'd hardcoded everything in, and turning that into an interactive dashboard would never work. So the project was refactored into


## Key Technologies

QMFG is written almost entirely in python. Notable libraries include:
* **Flask** -- web app framework with useful extensions:
    * **Flask-SQLAlchemy** -- ORM support via SQLAlchemy
    * **Flask-WTF** -- form validation and security via WTForms
    * **Flask-Migrate** -- CLI tools for database migration via Alembic
    * **Flask-Login** --  user access control and session handling
* **Jinja2** -- endpoint templating/dynamic styling
* **pandas** -- Data analysis/manipulation
    * Production performance and reporting
    * Scheduling logic done entirely within datetime-indexed dataframes
* **python-dotenv** -- environment variable handling
* **venv** -- virtual environment handling
* **bokeh**, **matplotlib** -- data visualization

SQLite provided a simple and easy SQL deployment during development, for production deployment a dedicated MySQL server would be best.

QMFG also includes custom ETL tools for acquiring data from internal NAS:
* Plaintext csv generated by equipment sensors
* Operator reports saved in Excel format (.xlsx)

Considerable time was spent re-familiarizing myself with HTML/CSS and creating a UI/UX that was functional and pleasing. While not the main focus of this project, I still wanted the front-end to express my initial vision accurately -- and eventually it did!


## Dependencies

HTTP Server -- production-grade web server (Apache, Nginx)

WSGI Server -- interface between the web server and the python backend (mod_wsgi, Gunicorn)

MySQL Server -- better scalability than the SQLite currently implemented, not required but certainly close

SSO Integration -- inbuilt login functionality is minimal and not intended for production use

run `pip install -r requirements.txt` to install python dependencies


## Lessons Learned

There's always more abstraction to consider. The importance of designing systems ahead of building them is shown by the numerous refactorizations this project has undergone.

If I were to do this over, I would start with a frontend framework such as React.js and develop that from the ground up. The additional capabilities provided by Javascript would allow greater use of the modern visual style I've strived to implement:
* Dragging and dropping a work order to load, park, etc.
* Tabbed pages for process groups
* Scalable dashboard views, e.g. 1-hour to 1-year


## Helpful Links

* [Miguel Grinberg's *The Flask Mega-Tutorial.*](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world)

## License

