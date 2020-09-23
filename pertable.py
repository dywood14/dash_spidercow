import os, sys, csv
import pandas as pd

# All percentages must be entered in percent value instead of decimal
# i.e. -35 (O) / -0.35 (X)

def PerCalc(cur_percent, cur_price, des_percent):

  dif_percent_deci = (des_percent - cur_percent) *0.01
  des_price = round((cur_price * (1+dif_percent_deci)), 2)

  des_price = f"{des_price:,}"
  return des_price  #expected output: 2.14 (as in $2.14)

def PerCalc_PO(close_price, des_price):

  des_percent = (des_price - close_price) / close_price

  des_percent = round((des_percent * 100), 2)
  return des_percent   #expected output: -61.26  (as in -61.26%)

def PerCalc_from_Close(close_price, des_percent):
  des_price = close_price + (close_price * (des_percent*0.01))
  des_price = round(des_price, 2)
  return des_price

"""
def PerTab(cur_percent, cur_price, mar):
  cur_percent_deci = round((cur_percent *0.01),4)

  base_percent_diff_deci = round((-0.15 - cur_percent_deci),4)
  base_percent_deci = base_percent_diff_deci + cur_percent_deci
"""
def PerTab(close_price, mar):
  exit=7

  per_dict={}

  for i in range(15, 91):
    # Index / Exit / Buy / Sell / Tags
    #per_dict['-{}%'.format(i)] = [PerCalc(cur_percent, cur_price, -(i+exit)), PerCalc(cur_percent, cur_price, -i), PerCalc(cur_percent, cur_price, (-i+mar)), '-']
    per_dict['-{}%'.format(i)] = [PerCalc_from_Close(close_price, -(i+exit)), PerCalc_from_Close(close_price, -i), PerCalc_from_Close(close_price, (-i+mar)), '-']

  per_dict['-16%'][3]= 'Minimum Entry'
  per_dict['-17%'][3]= '(-1%)'
  per_dict['-18%'][3]= '(-2%) CEO/Exec Depature'
  per_dict['-19%'][3]= '(-3%)'
  per_dict['-20%'][3]= '(-4%): Downgrade'
  per_dict['-21%'][3]= '(-5%)'
  per_dict['-22%'][3]= '(-6%)'
  per_dict['-23%'][3]= 'High Risk or CFO Depature'
  per_dict['-25%'][3]= 'On the day of Reverse Split'

  per_dict['-35%'][3]= 'Profit(e) / Business Update'
  per_dict['-40%'][3]= 'Delisting Notice / Reverse Split / Public Offering / Profitable Quarter/ Lost Customers'
  per_dict['-50%'][3]= 'Phase 1 Failure/News / Quarterly Loss(e)'
  per_dict['-55%'][3]= 'Phase 2 News'
  per_dict['-60%'][3]= 'Phase 2 Failure'
  per_dict['-65%'][3]= 'Ch 11 News, Reported Loss'
  per_dict['-70%'][3]= 'Ch 11 Announcement'
  per_dict['-75%'][3]= 'Voluntary Delist'
  per_dict['-80%'][3]= 'Phase 3 News'
  per_dict['-85%'][3]= 'Phase 3 Fail / Ch 7 Announce / Pink Sheet(e)'
  per_dict['-90%'][3]= 'Ch 7 / Pink Sheet(e)'

  df = pd.DataFrame(list(per_dict.values()), list(per_dict.keys()), columns=['Exit @','Buy @','Sell @','Tags'])
  return df

def main():
  PerTab(cur_percent, cur_price, mar)

if __name__ == '__main__':
  cur_price = round(float(sys.argv[1]),2)
  cur_percent = round(float(sys.argv[2]),4)
  mar = round(float(sys.argv[3]),4)
  main()