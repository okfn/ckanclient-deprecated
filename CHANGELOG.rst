Changelog
=========

v0.11 2013-06-12
----------------

  * Default URL changed from thedatahub.org to datahub.io

v0.10
-----

  * Add support for CKAN's Action API
  * GET methods now send API key too
  * Removed changeset functions
  * Added a script for creating a CSV dump of a CKAN instance
  * Add support for uploading files to the CKAN FileStore via the Storage API
  * Add support for uploading data files to the CKAN DataStore via the
    Data API (merge datastore-client into ckanclient)

v0.9 2011-08-09
---------------

  * Default URL changed to thedatahub.org
  * Guard against 301 redirection, which loses POST contents


v0.8 2011-07-20
---------------

  * More detailed exceptions added
  * Some Python 3 compatibility
  

v0.7 2011-01-27
---------------

  * Package search returns results as a generator
    (rather than a list that needs to be paged)
  

v0.5 2010-12-15
---------------

  * Exception raised on error (more Pythonic)
  

v0.4 2010-10-07
---------------

  * Form API added
  * Package name editing
  * Groups added
  * Output can be verbose and use logger
  * Query API version
  * Sends API key via additional header
  

v0.3 2010-04-28
---------------

  * General usability improvements especially around error messages. 
  * Package Relationships added
  * Package deletion fixed
  * Changeset entities added
  * Improved httpauth (thanks to will waites)


v0.2 2009-11-05
---------------

  * Search API support added
  * Improved package support to include additional fields such as 'extras'
  * Support tag and group entities in addition to package
  * Compatibility changes: CkanClient base_location (now should point to base
    api e.g. http://ckan.net/api rather than http://ckan.net/api/rest)


v0.1 2008-04
------------

  * Fully functional implementation for REST interface to packages
