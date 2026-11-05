SELECT strptime("Date", '%d/%m/%Y')::DATE AS day,
"Hour"::INTEGER AS hour, "Rented Bike Count"::DOUBLE AS y,
"Functioning Day" = 'Yes' AS operating, "Holiday" = 'Holiday' AS holiday,
"Temperature" AS temp, "Humidity" AS humidity, "Rainfall" AS rain,
"Snowfall" AS snow, "Wind speed" AS wind, "Visibility" AS visibility,
"Dew point temperature" AS dew, "Solar Radiation" AS solar
FROM read_csv('/hal-light/examples/seoul-bike-sharing-demand/question/data.csv', all_varchar=true) ORDER BY day, hour