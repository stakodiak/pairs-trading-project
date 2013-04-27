#include <vector>
#include <fstream>
#include <queue>
#include <map>
#include <algorithm>
#include <string>
#include <math.h>
#include <iomanip>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define DIRECTORY "data"

/* Pair structure for priority queue */
struct Pair {
Pair( int i, int j, float value ) :
		i_(i), j_(j), metric(value) { }

	int i_, j_;
	float metric;
	 };
bool operator>( const Pair& lhs, const Pair& rhs ) {
  return lhs.metric < rhs.metric;
  }

/* Represents each ticker */	
class Stock {
	/* Each Stock is identified by its ticker name */
	char *ticker;
	bool is_valid;
	/* Add all closing prices to aray */
	float prices_array[365];
	float returns_array[365];
	int num_prices;
	int num_returns;

	/* Statistical metrics */
	float mean, variance, SD;
	// avg. mean - 0.000609248145650708
	/* For identifying candidates */
	int num_reversions;
	float chi_square;
public:
	
	Stock () { } 
	Stock (char *name) {
		ticker = (char*) malloc (5 * sizeof (char));
		strcpy (ticker, name);
		num_prices = 0;
		is_valid = true;
	}

	void add_price (float price) {

		prices_array[num_prices] = price;
		num_prices++;

	}
	
	char *get_name () { return ticker; }
	bool process () {

		/* Generate list of returns  */
		num_returns = 0;
		for (int i = 0; i < (num_prices - 1); i++) {
			returns_array[num_returns] = log (prices_array[i + 1]) - log (prices_array[i]);
			num_returns++;
		}

		/* Calculate mean */
		float sum = 0.0;
		for (int i = 0; i < num_returns; i++) 
			sum += returns_array [i];
		mean = sum / num_returns;

		/* Calculate variance and mean reversions */
		double sum_squared_distances = 0.0;
		num_reversions = 0;
		bool is_crossed = (returns_array[0] >= mean);
		for (int i = 0; i < num_returns; i++) {
			sum_squared_distances += (returns_array[i] - mean) * (returns_array[i] - mean);
			if (is_crossed != (returns_array[i] >= mean)) {
				num_reversions++;
				is_crossed = (returns_array[i] >= mean);
			}
		}

		variance = sum_squared_distances / (num_returns - 1);
		/* Calculate SD */
		SD = sqrt (variance);

		/* Decide if valid stock */
		if (num_returns != 252) 
			is_valid = false;	
		if (variance < 0.0002)
			is_valid = false;
		if(mean < 0.001 && mean > -0.001)
			is_valid = false;
		return is_valid;
	}

	int get_returns () { return num_returns; }
	
	float get_variance() { return variance; }

	float return_at (int index) { 
		if (index < 0 || index > num_returns)
			return 0;
		return returns_array[index]; }

	float std_dev () { return SD; }

	float avg_return () { return mean; }

};


float get_corr (Stock s1, Stock s2) {

	int num_returns = s1.get_returns();
	float mean_A = s1.avg_return();
	float mean_B = s2.avg_return();
	float sum_distances = 0.0;
	for (int k = 0; k < num_returns; k++) 
		sum_distances += (s1.return_at(k) - mean_A) * (s2.return_at(k) - mean_B);
	float covar = sum_distances / (num_returns - 1);

	float correlation = covar / (s1.std_dev() * s2.std_dev());
	return correlation;
}
float get_chi (Stock s1, Stock s2) {

	float correlation =  get_corr (s1, s2);

	return s1.get_variance() *  (1.0 - correlation * correlation);

}

bool check_name (char *t1, char *t2) {
	
	/* If names are too similar */
	if (t1[0] == t2[0])
		if (t1[1] == t2[1])
			return false;
	return true;
}

int main () {

	/* Access stocks by ticker name */
	std::map<std::string, Stock> stock_list;

	/* Load all files */
	//printf ("Parsing stock files in 'data/'...");
	fflush (stdout);
	char *data =  (char*) malloc (256 * sizeof (char));
	FILE *input;
	int month, day, num_prices = 0;
		
	for (month = 1; month <= 12; month++) 
		for (day = 1; day <= 31; day++) {
			
			/* Generate all filenames */
			char *file_name = (char*) malloc (sizeof (data));
			sprintf (file_name, "%s/NYSE_2011%02d%02d.txt", DIRECTORY, month, day);
			input = fopen(file_name, "r");
			/* Ignore missing files */
			if (input == NULL) {
				continue;
			}
			num_prices++;
			//printf ("%02d %02d\n", month, day);			
			/* Skip CSV header information */
			fscanf (input, "%s", data);

			/* Scrape all data from file */
			while (fscanf(input, "%s", data) != EOF) {
	
				/* Get ticker name */
				char *ticker_name = (char*) malloc (16 * sizeof(char));
				int ticker_loc  = strchr (data, ',') - data;
				sprintf (ticker_name, "%.*s", ticker_loc, data);
				
				/* Extract closing price */
				char *price = (char*) malloc (16 * sizeof(char));
				int price_end = strrchr (data, ',') - data;
				sprintf (price, "%.*s", price_end, data);
				int price_beg = strrchr (price, ',') - price + 1;
				int price_size = price_end - price_beg;
				sprintf(price, "%.*s", price_size, price + price_beg);
				
				float closing_price = atof (price);

				//printf("%s -> %f\n", ticker_name, closing_price);

				if (stock_list.find (ticker_name) == stock_list.end())
					stock_list [ticker_name] = Stock(ticker_name);

				stock_list [ticker_name].add_price (closing_price);
			}
	}

	//printf(" Done.\n");	
	//printf ("Processing series...");
	fflush (stdout);
	
	/* Process all stocks */
	int num_returns = num_prices - 1;
	std::vector<Stock> stocks;
	std::map <std::string, Stock>::iterator it;
	for (it = stock_list.begin(); it != stock_list.end(); it++)
		if(it->second.process()) 
			stocks.push_back (it->second);
	//printf (" Done.\n");

	/* Identify candidates */
	//printf ("Identifying candidates...");
	fflush (stdout);
	const int num_stocks = stocks.size();
	
	// Use priority queue for easy identification of top candidates
	std::priority_queue<Pair, std::vector<Pair>, std::greater<Pair> > pq;
	for (int i = 0; i < num_stocks; i++) {
		Stock s1 = stocks.at(i);
		for (int j = 0; j < i; j++) { 
			Stock s2 = stocks.at(j);
			float chi = get_chi (s1, s2);
			if (chi < 0.99) 
				pq.push (Pair(i, j, chi));
			printf ("%f\n", chi);
		}
	}

	//printf (" Done.\n");

	/* Print top 100 */
	//printf ("\nTop 100 candidates: \n");
	int count = 0;
	while (count < 1000) {
		Pair p =  pq.top();
		pq.pop();
		char *t1 = stocks.at (p.i_).get_name();
		char *t2 = stocks.at (p.j_).get_name();
		if (check_name (t1, t2)){
			//printf ("%f (%s, %s)\n", p.metric, t1, t2);
			count++;
		}
	}
	//printf ("\n%i stocks in list.\n", num_stocks);
	
	fflush (stdout);
	/* TEST APL 
	Stock test = stocks.at(1);
	char *name = test.get_name();
	printf ("Testing '%s' - \n", name);
	printf ("Avg. return: %f\n", stock_list [name].avg_return());
	printf ("Var: %f\n", stock_list [name].get_variance());
	printf ("CV: %f (%s)\n", get_covar (test, stocks.at(2)), stocks.at(2).get_name());
	printf ("SD: %f\n", stock_list [name].std_dev());
	printf ("Returns: %i\n", stock_list [name].get_returns());
	*/
	
}
