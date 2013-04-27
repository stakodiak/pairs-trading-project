# plot.py - Plots given tickers.
import sys, os
import math
import tempfile
from string import Template

	
def get_data(ticker, index=1):
# Returns dictionary with ticker information.

	# Put in temp. file for later access
	data = dict()
	temp = tempfile.NamedTemporaryFile (delete=False)

	# Get all closing prices for ticker
	closing_prices = []
	for m in range(1, 12 + 1):
		for d in range(1, 31 + 1):
			try:	
				file_name = "data/NYSE_2011{:02}{:02}.txt".format (m, d)
				daily_tick_data = open(file_name,  "rb")
				# <ticker>,<date>,<open>,<high>,<low>,<close>,<vol>
				for line in daily_tick_data:
					stocks = line.split (',')
					if stocks[0] == ticker:
						price = float(stocks[-2])
						closing_prices.append (price)

				daily_tick_data.close()
			except Exception:
				pass

	# Check for valid series
	if len (closing_prices) == 0:
		print "Error: No closing prices found for '{}'.".format(ticker)
		sys.exit(1)

	# Convert into returns
	returns_list = []
	for i in range(len(closing_prices) - 1):
		r = math.log(closing_prices[i + 1]) - math.log(closing_prices[i])
		returns_list.append(r)

	# Switch to moving average process
	moving = moving_average (returns_list, 20)
	for r in moving:
		temp.write ("{}\n".format(r))

	# # Uncomment for working with moving-average data
	#returns_list = moving	

	# Calculate mean
	total = 0.0
	for r in returns_list:
		total += r
	mean = total / len (returns_list)

	# Get variance + SD
	squared_sum = 0.0
	for r in returns_list:
		squared_sum += (r - mean) * (r - mean)
	variance = squared_sum / ( len (returns_list) - 1)
	SD = math.sqrt (variance)
	
	# Print results
	column1 = 12
	column2 = 5
	print "{0:>{l}} - '{1}'".format("Ticker", ticker, l = 12 - 1, l2=column2)
	print "{0:>{l}}:  {1:>{l2}f}".format ("Avg. Return", mean, l=column1, l2=column2)
	print "{0:>{l}}:  {1:>{l2}f}".format ("Variance", variance, l=column1, l2=column2)
	print "{0:>{l}}:  {1:>{l2}f}".format ("Std. Dev.", SD, l=column1, l2=column2)
	print "Num. returns:  {num}\n".format(num=len(returns_list))
	
	# Add all to dictionary
	# Uses index for working with gnuplot template
	data ['returns_file{}'.format(index)] = temp.name
	data ['moving{}'.format(index)] = moving
	data ['returns{}'.format(index)] = returns_list
	data ['mean{}'.format(index)] = mean
	data ['variance{}'.format(index)] = variance
	data ['SD{}'.format(index)] = SD
	data ['ticker{}'.format(index)] = ticker

	return data


def moving_average (series, time):
	moving = list()
	for i in range(len (series)):
		s = 0.0
		r = 0.0
		if i == 0:
			r = series [i] + series [i + 2] 
			r /= 2

		elif i < time:
			for j in range(i):
				s += series[j]
			r = s / i
		else:
			for j in range(time):
				s += series[i - j]
			r = s / time
		moving.append (r)
	return moving


def get_metric (s1, s2):
# Returns correlation between two series

	series1 = s1['returns1']
	m1 = s1['mean1']
	series2 = s2['returns2']
	m2 = s2['mean2']

	s = 0.0
	for i in range(len(series1)):
		s += (series1[i] - m1) * (series2[i] - m2)
	
	s /= (len(series1) - 1)

	return s / ((s1['SD1'] * s2['SD2']))

def plot_data (data1, data2=None):
# Invokes gnuplot with temporary script containing all time-series information

	out_file = 'plot.svg'
	data1['out_file'] = out_file
	
	# Plot y - gamma * x
	pairs_file = tempfile.NamedTemporaryFile()
	series = list()
	rho = get_metric (data1, data2)
	for i in range (len(data1['returns1'])):
		y = data2['returns2'][i]
		x = data1['returns1'][i]
		
		value = y -  rho * x
		series.append (value)
	# for value in moving_average (series, 20):
		pairs_file.write (str(value) + "\n")

	data1['pairs'] = pairs_file.name	
	data1['rho'] = "{:3f}".format(rho)
	temp = tempfile.NamedTemporaryFile()
	template = """
			set terminal svg size 980,640 fname 'Verdana, Helvetica, Arial, sans-serif' \
			fsize '10'
			set output '$out_file'

			# from gnuplotting
			set style line 12 lc rgb '#808080' lt 0 lw 1
			set grid back ls 12

			# automate 
			foo = 0.00
			set label "$ticker1 vs. $ticker2" at graph foo,1.1 left font "Courier,24"
			set label "Jan. 2011-Dec. 2011" at graph foo,1.05 left font "Courier New,20" tc rgb '#696969'

			set ylabel "Daily Returns" font "Courier New,16"
			set xlabel "Time" font "Courier New,16"

			set tmargin at screen 0.85
			set lmargin at screen 0.10
			#set title "Testing  Testing!" font "Times,20"
			unset border
			# color definitions
			set border linewidth 1.5
			set style line 1 lc rgb '#0060ad' lt 1 lw 1.5 pt 7 ps 1.5 # --- blue
			set style line 2 lc rgb '#008cfb' lt 1 lw 1 pt 7 ps 1.5 # --- blue
			set style line 3 lc rgb '#dd181f' lt 1 lw 1.5 pt 5 ps 1.5   # --- red
			set style line 4 lc rgb '#ed555a' lt 1 lw 1 pt 5 ps 1.5   # --- red
			set style line 5 lc rgb '#60ad00' lt 1 lw 1.5 pt 5 ps 1.5   # --- red
			f(x) = $SD1 + $mean1
			g(x) = $SD2 + $mean2
			plot [5:259] '${returns_file1}' every 1 title '$ticker1' with linespoints ls 1 smooth unique, \
				-1* f(x) notitle with lines linestyle 2, \
				g(x) notitle with lines linestyle 2, \
				-1* g(x) notitle with lines linestyle 4, \
				f(x) notitle with lines linestyle 4, \
			 '${returns_file2}' every 1 title '$ticker2' with linespoints ls 3 smooth unique"""

	# Change bool to plot linear combaination
	if False:
		template += """, \
			 '${pairs}' every 1 title 'rho=$rho' with linespoints ls 5 smooth unique
		"""
	data1.update(data2)
	script = Template (template).substitute (data1)
	temp.write(script)
	temp.flush()

	os.popen ("gnuplot {}".format (temp.name))
	temp.close()

	print out_file, 'printed'

	
def main ():

	if len(sys.argv) != 3:
		print "Error. Please supply two ticker names."

	else:
		# Return the data in a index-formatted dictionary
		d1 = get_data (sys.argv[1], 1)
		d2 = get_data (sys.argv[2], 2)

		# Plot data with temp. gnuplot script
		plot_data (d1, d2)


if __name__ == "__main__":
	main()
