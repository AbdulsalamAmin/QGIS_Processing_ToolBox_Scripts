#from __future__ import division (Not used in place the divisor is converted to float e.g. x/float(y))
##[OSM-History]=Group
##Host=String localhost
##Port=Number 5432
##Database=String hist_osm_pb 
##User=String postgres
##Password=String a


from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtSql import *
from qgis.core import *
from processing.tools.vector import VectorWriter
import psycopg2
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pylab

#description     :This file creates a plot: Calculates the development of invalid polygons (total amount and percentage)
#author          :Sukhjit Singh Sehra modified the code of Christopher Barron @ http://giscience.uni-hd.de/
#date            :11.10.2016
#version         :1.0
#usage           :This script is designed to work with historic data imported into PostgreSQL database using osm-hisotry-renderer tool, for more information please visit https://github.com/sukhjitsehra/iOSMAnalyzer
#Notes            : mind that by default DB user is considered as "postgres". please look at "OWNER TO postres" in the code.

#For creating connection with DB
try:
  conn_string="dbname= %s user= %s host= %s password= %s" %(Database, User, Host, Password)
  #conn_string="dbname= %s user= %s host= %s password= %s" %(db.g_my_dbname, db.g_my_username, db.g_my_hostname, db.g_my_dbpassword)
  #print "Connecting to database\n->%s" % (conn_string)
      
# Verbindung mit der DB mittels psycopg2 herstellen
  conn = psycopg2.connect(conn_string)
  #QMessageBox.critical(None, "About Layer", "Connection to DB Sucessful")
except:
 QMessageBox.critical(None, "About Layer", "Connection to database Failed")

# Create a new cursor object
cur1 = conn.cursor()

# Execute SQL query. For more than one row use three '"'
try:
  cur1.execute("""
-- Amount of currently valid polygons/lines and amount of currently valid invalid polygons/lines
SELECT	
	-- invalid polygons:today
	(SELECT count(id) 
	FROM 
		hist_polygon 
	WHERE visible = 'true' AND
		(ST_IsValid(geom) = false) AND
		(version = (SELECT max(version) FROM hist_polygon AS h WHERE h.id = hist_polygon.id AND
			(valid_from <= generate_series AND (valid_to >= generate_series OR valid_to is null))) 
		AND minor = (SELECT max(minor) FROM hist_polygon AS h WHERE h.id = hist_polygon.id AND h.version = hist_polygon.version AND
			(valid_from <= generate_series AND (valid_to >= generate_series OR valid_to is null))))
	) AS poly_invalid, generate_series
FROM generate_series(
	(SELECT date_trunc ('month',(
		SELECT MIN(valid_from) FROM hist_polygon)) as foo),  -- Select minimum date (month)
	(SELECT MAX(valid_from) FROM hist_polygon)::date,	-- Select maximum date
	interval '1 month')
""")

except:
    QMessageBox.critical(None, "About Layer", "First Query could not be executed")

# Getting a list of tuples from the database-cursor (cur)
data_tuples1 = []
for row1 in cur1:
    data_tuples1.append(row1)

# END Execute SQL query1. 
    
# Datatypes of the returning data (invalid Polygons)
datatypes1 = [('col1', 'i4'), ('date', 'S20')]

# Data-tuple and datatype
data1 = np.array(data_tuples1, dtype=datatypes1)

# Date comes from 'col1'
col1 = data1['col1']
col2 = data1['date']



# START Execute SQL query2.
cur2 = conn.cursor()

try:
  cur2.execute("""
-- Amount of currently valid polygons/lines and amount of currently valid invalid polygons/lines
SELECT	
	(SELECT count(id) 
	FROM 
		hist_polygon 
	WHERE visible = 'true' AND
		(version = (SELECT max(version) FROM hist_polygon AS h WHERE h.id = hist_polygon.id AND
			(valid_from <= generate_series AND (valid_to >= generate_series OR valid_to is null))) 
		AND minor = (SELECT max(minor) FROM hist_polygon AS h WHERE h.id = hist_polygon.id AND h.version = hist_polygon.version AND
			(valid_from <= generate_series AND (valid_to >= generate_series OR valid_to is null))))
	) AS poly_total, generate_series
FROM generate_series(
	(SELECT date_trunc ('month',(
		SELECT MIN(valid_from) FROM hist_polygon)) as foo),  -- Select minimum date (month)
	(SELECT MAX(valid_from) FROM hist_polygon)::date,	-- Select maximum date
	interval '1 month')
  """)

except: 
    QMessageBox.critical(None, "About Layer", "First Query could not be executed")
    
# Getting a list of tuples from the database-cursor (cur)
data_tuples2 = []
for row2 in cur2:
    data_tuples2.append(row2)

# END Execute SQL query2.

# Datatypes of the returning data (total amount of Polygons)
datatypes2 = [('col2', 'i4'), ('date', 'S20')]

# Data-tuple and datatype
data2 = np.array(data_tuples2, dtype=datatypes2)

# Date comes from 'col1'
col2 = data2['col2']


#Plot


# Figure and Subplot
fig = plt.figure()
ax1 = fig.add_subplot(111)

# Converts date to a manageable date-format for matplotlib
dates = mdates.num2date(mdates.datestr2num(data1['date']))

# Create barchart (x-axis=dates, y-axis=col1, 
ax1.bar(dates, col1, width=15, align='center', color = '#2dd700')

# Rotate x-labels on the x-axis
fig.autofmt_xdate()



# Percentage of invalid polygons from total amount of polygons
quotients = [x *100 / float(y) for x, y in zip(col1, col2)]



# Adds the second y-axis (Percentage of invalid polygons from total amount of polygons)
ax2 = ax1.twinx()
ax2.plot(dates, quotients, linewidth=2, color = '#ff6700')

# Place a gray dashed grid behind the thicks (only for y-axis)
ax1.yaxis.grid(color='gray', linestyle='dashed')

# Label x axis
plt.xlabel('Date')

# Set colors for axis and their label
ax1.set_ylabel('Number of invalid Polygons', color='#2dd700')
for tl in ax1.get_yticklabels():
    tl.set_color('black')
    
ax2.set_ylabel('Percentage of invalid Polygons from all Polygons [%]', color='#ff6700')
for tl in ax2.get_yticklabels():
    tl.set_color('black')
    
# Set a limit to y-axis from the percentage-axis
ax2.set_ylim(top=5)

# Plot-title
plt.title("Development of invalid Polygons")

# Save plot to *.jpeg-file
plt.savefig('pics/c6_invalid_poly.jpeg')

plt.clf()