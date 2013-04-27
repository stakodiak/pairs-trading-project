# python_test.py - compute properties of a stock to compare to C++ calculations
import sys, math
import csv

def fill_stock(ticker):
	ticker_prices = []
	for m in range(1, 12 + 1):
		for d in range(1, 31 + 1):
			try:
				file_name = "data/NYSE_2011{:02}{:02}.txt".format (m, d)
				daily_tick_data = open(file_name, "rb")
				stock_list = csv.reader(daily_tick_data)

				for stock in stock_list:
					if stock[0] == ticker:
						ticker_prices.append (float(stock[5]))

				daily_tick_data.close()
			except Exception:
				pass
	return ticker_prices

def get_returns(price_list):
	return_list = []

	for i in range(len(price_list) - 1):
	#   r = (price_list[i + 1] - price_list[i]) / price_list[i]
		r = math.log(price_list[i + 1]) - math.log(price_list[i])
		return_list.append(r)
	
	return return_list

		
def get_avg_return (returns_list):
	total_sum = 0.0
	for r in returns_list:
		total_sum += r
	return total_sum / len(returns_list)

def get_variance (returns_list, mean_return):
	summation = 0.0
	for r in returns_list:
		summation += (mean_return - r) * (mean_return - r)
	
	return summation / (len(returns_list) - 1)

class Ticker:
	pass

def get_correlation (T1, T2):
	
	s = 0.0
	for i in range (len(T1.returns)):
		s += (T1.returns[i] - T1.avg_return) * (T2.returns[i] - T2.avg_return)
	covar =  s / (len(T1.returns) - 1)

	return covar / (T1.SD * T2.SD)

def print_ticker(ticker_name):

	ticker = Ticker()
	
	ticker.ticker = ticker_name
	ticker.prices = fill_stock(ticker_name)
	
	ticker.returns = get_returns (ticker.prices)
   	ticker.avg_return = get_avg_return (ticker.returns)
	ticker.variance = get_variance (ticker.returns, ticker.avg_return)
	ticker.SD = math.sqrt(ticker.variance)

	# Print details
	column1 = 12
	column2 = 5
	print "{0:>{l}} - '{1}'".format("Ticker", ticker.ticker, l = 12 - 1, l2=column2)
	print "{0:>{l}}:  {1:>{l2}f}".format ("Avg. Return", ticker.avg_return, l=column1, l2=column2)
	print "{0:>{l}}:  {1:>{l2}f}".format ("Variance", ticker.variance, l=column1, l2=column2)
	print "{0:>{l}}:  {1:>{l2}f}".format ("Std. Dev.", ticker.SD, l=column1, l2=column2)
	print "Num. returns:  {num}\n".format(num=len(ticker.returns))
	
	return ticker

def main():
	ticker = "AA"
	if len(sys.argv) >=  2:
		ticker1 = print_ticker(sys.argv[1])
	
	if len(sys.argv) == 3:
		
		ticker2 = print_ticker(sys.argv[2])
		print get_correlation (ticker1, ticker2)

if __name__ == '__main__':
	main()
