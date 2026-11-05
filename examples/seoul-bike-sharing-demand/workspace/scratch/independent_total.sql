SELECT sum(rentals) total,sum(n) n FROM (SELECT season,h,count(*) n,sum(y) rentals FROM hours GROUP BY 1,2);
