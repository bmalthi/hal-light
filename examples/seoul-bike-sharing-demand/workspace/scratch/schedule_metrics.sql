SELECT split,model,count(*) n,avg(abs(y-schedule_pred)) mae,sqrt(avg((y-schedule_pred)^2)) rmse,sum(abs(y-schedule_pred))/sum(y) wape FROM scored GROUP BY 1,2 ORDER BY 1,mae;
