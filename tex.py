# tex.py - Plots given tickers. Returns LaTeX markup.
import sys, os
import math
import tempfile
from string import Template


def main ():
	if len(sys.argv) < 3:
		print "Error. Please supply two ticker names."
	else:
		# Return the data in a index-formatted dictionary
		d1 = get_data (sys.argv[1], 1)
		d2 = get_data (sys.argv[2], 2)

		# Plot data with temp. gnuplot script
		plot_data (d1, d2)


class Series:
	mean = 0.0
	variance = 0.0
	SD = 0.0
	num_stocks = 0
	series = None
	num_reversions = 0
	reversions = 0

	def __init__(self, series):
		
		# Save series
		self.series = series
		self.num_stocks = len (series)

		# Calculate mean
		total = 0.0
		for i in series:
			total += i
		mean = total / len(series)
		self.mean = mean

		# Calculate variance
		squared_sums = 0.0
		for i in series:
			squared_sums += (i - mean) * (i - mean)
		variance = squared_sums / (len(series) - 1)
		self.variance = variance

		# Calculate SD
		SD = math.sqrt (variance)
		self.SD = SD

		# Count mean reversions
		is_crossed = (series[0] >= mean)
		num_reversions = 0
		time_count = 0
		reversions = list()
		for i in series:
			time_count += 1
			if (is_crossed != (i >= mean)):
				reversions.append(time_count)
				time_count = 1
				num_reversions += 1
				is_crossed = (i >= mean)
		self.reversions = reversions
		self.num_reversions = num_reversions


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
		r = math.log(closing_prices[i])
		returns_list.append(r)

	# Switch to moving average process
	moving = moving_average (returns_list, 20)
	for i in range(len(moving) - 1):
		r = moving[i]

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
	s = Series (returns_list)
	column1 = 12
	column2 = 5
	print "{0:>{l}} - '{1}'".format("Ticker", ticker, l = 12 - 1, l2=column2)
	print "{0:>{l}}:  {1:>{l2}f}".format ("Avg. Return", mean, l=column1, l2=column2)
	print "{0:>{l}}:  {1:>{l2}f}".format ("Variance", variance, l=column1, l2=column2)
	print "{0:>{l}}:  {1:>{l2}f}".format ("Std. Dev.", SD, l=column1, l2=column2)
	print "Num. returns:  {num}".format(num=len(returns_list))
	print "  Reversions:  {}\n".format (s.num_reversions)
	
	# Add all to dictionary
	if "--moving" in sys.argv:
		data['returns'] = moving
	else:
		data['returns'] = returns_list
	data['ticker'] = ticker
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
# Returns gamma between two series
	# list of returns
	s1 = s1['returns']
	s2 = s2['returns']

	# get metrics for calculation
	m1 = Series(s1).mean
	m2 = Series(s2).mean
	var = Series(s2).variance
	covar = 0.0

	# calculate gamma
	for i in range(len(s1)):
		covar += (s1[i] - m1) * (s2[i] - m2)
	covar /= (len(s1) - 1)
	gamma = covar / var

	return gamma


def plot_data (A, B):
# First outputs LaTeX source for pair then portfolio

	out_file = 'plot.tex'
	template = """
% Needs Tikz and PGFPlots installed

\documentclass[border=10mm]{standalone}
\usepackage{tikz}
\usepackage{pgfplots}
\pgfplotsset{width=15cm, height=10cm}

\\begin{document}
\\begin{document}
\\begin{figure}
	\\begin{tikzpicture}
	  \\begin{axis}[
	  	title={\large $title},
		xmin=0,
		xmax=260,
		xlabel=Time (days),
		ylabel=$$\ln$$(Portfolio Prices)]
		$plot
		\legend {$legend}
	  \end{axis}
	\end{tikzpicture}
\end{figure}
\end{document}
	"""
	template = Template(template)
	
	coordinates = """
	  \\addplot[color=$color] coordinates {
$list
	  };
	"""
	plot = Template(coordinates)

	# This could be less nested probably
	plotA = plot.substitute({'color': 'red',
	'list': "\n".join([' ' * 8 + "({},{})".format(x + 1, A['returns'][x]) for x in range(len(A['returns']))])})
	plotB = plot.substitute({'color': 'blue',
	'list': "\n".join([' ' * 8 + "({},{})".format(x + 1, B['returns'][x]) for x in range(len(B['returns']))])})
	legend = "{}, {}".format(A['ticker'], B['ticker'])
	title = ""

	# Save to file
	script = template.substitute ({'legend': legend, 'plot': plotA + plotB, 'title': title})	
	out = open(out_file, 'w')
	out.write(script)
	out.close()
	print out_file, "printed"

	# Build portfolio data
	P = list()
	gamma = get_metric (A, B)
	for i in range (len(A['returns']) - 1):
		y = A['returns'][i]
		x = B['returns'][i]
		value = y - gamma * x 
		P.append (value)

	# Print results
	s = Series (P)
	column1 = 12
	column2 = 5
	print "{0:>{l}} - '{1}'".format("Portfolio", "", l = 12 - 1, l2=column2)
	print "{0:>{l}}:  {1:>{l2}f}".format ("Avg. Return", s.mean, l=column1, l2=column2)
	print "{0:>{l}}:  {1:>{l2}f}".format ("Variance", s.variance, l=column1, l2=column2)
	print "{0:>{l}}:  {1:>{l2}f}".format ("Std. Dev.", s.SD, l=column1, l2=column2)
	print "Num. returns:  {num}".format(num=len(P))
	print "  Reversions:  {}\n".format (s.num_reversions)
	
	# Save portfolio to file
	portfolio = plot.substitute({'color': 'violet', 
	'list': "\n".join([' ' * 8 + "({},{})".format(x + 1, P[x]) for x in range(len(P))])})
	legend = "{} \minus ($\gamma$ \\times {})".format(A['ticker'], B['ticker'])
	title = "Portfolio"

	# Save script to file
	out_file = "portfolio_" + out_file
	script = template.substitute ({'legend': legend, 'plot': portfolio, 'title': title})	
	out = open(out_file, 'w')
	out.write(script)
	out.close()
	print out_file, "printed"
	
if __name__ == "__main__":
	main()
