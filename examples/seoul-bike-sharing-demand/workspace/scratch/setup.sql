CREATE TEMP VIEW raw AS SELECT * FROM read_csv_auto('/hal-light/examples/seoul-bike-sharing-demand/question/data.csv', all_varchar=true);
CREATE TEMP VIEW hours AS SELECT strptime("Date",'%d/%m/%Y')::DATE d,"Hour"::INT h,"Rented Bike Count"::DOUBLE y,
"Temperature"::DOUBLE temperature,"Humidity"::DOUBLE humidity,"Wind speed"::DOUBLE wind,"Visibility"::DOUBLE visibility,
"Dew point temperature"::DOUBLE dew,"Solar Radiation"::DOUBLE solar,"Rainfall"::DOUBLE rain,"Snowfall"::DOUBLE snow,
"Seasons" season, "Holiday" holiday, "Functioning Day"='Yes' functioning,
CASE WHEN dayofweek(strptime("Date",'%d/%m/%Y')) IN (0,6) OR "Holiday"='Holiday' THEN 'Off day' ELSE 'Workday' END daytype
FROM raw;