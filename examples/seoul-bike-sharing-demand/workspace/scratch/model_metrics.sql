SELECT split,model,count(*) n,avg(abs(y-pred)) mae,sqrt(avg((y-pred)^2)) rmse,sum(abs(y-pred))/sum(y) wape,sum(pred-y)/sum(y) bias FROM scored WHERE functioning GROUP BY 1,2 ORDER BY 1,mae;
