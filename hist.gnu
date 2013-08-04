# generates histogram from data file.
# range
min = .0
max = .03

# style the graph
set term svg size 980, 640 fname 'Courier' fsize '10'
set style line 12 lc rgb '#808080' lt 0 lw 1
set grid back ls 12
set tmargin at screen 0.85
set lmargin at screen 0.10
#set offset graph 0.02, 0.02, 0.02, 0.0
unset border
set border linewidth 1.5
set label "Distribution of Chi-Squares" at graph 0.0,1.1 left font "Courier,24"
set label sprintf("Range: [%.2f, %.2f]",min,max) at graph 0.0,1.05 left font "Courier New,20" tc rgb '#696969'
set output "histogram.svg"

# number of intervals
n = 100
width = (max - min) / n 

# generate histogram
hist(x, width) = width * floor(x / width) + width / 2.0
set xrange [min:max]
set yrange [0:]
#set xtics min,(max-min)/5.0,max axis
set boxwidth width*0.9
set tics out nomirror
set xlabel "x" font "Courier New,16" 
set ylabel "Frequency" font "Courier New,16" 
set style fill pattern 6 border

# plot
plot "chi.txt" u (hist($1,width)):(1.0) smooth freq w boxes lc rgb"green" notitle
